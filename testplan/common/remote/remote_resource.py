import getpass
import itertools
import os
import sys
from typing import Callable, Iterator, List, Tuple, Union, Dict, Optional

from schema import Or

import testplan
import testplan.runnable
from testplan.common.config import ConfigOption
from testplan.common.entity import Entity, EntityConfig
from testplan.common.utils.path import (
    module_abspath,
    fix_home_prefix,
    pwd,
    makedirs,
    rebase_path,
    is_subdir,
)
from testplan.common.utils.process import execute_cmd, LogDetailsOption
from testplan.common.utils.remote import (
    copy_cmd,
    link_cmd,
    ssh_cmd,
    mkdir_cmd,
    worker_is_remote,
    filepath_exist_cmd,
    IS_WIN,
    rm_cmd,
)


class WorkerSetupMetadata:
    """
    Metadata used on worker setup stage execution.
    Pushed dirs and files will be registered for deletion at exit.
    """

    def __init__(self) -> None:
        self.delete_pushed = False
        self.push_dirs = []
        self.push_files = []
        self.setup_script = None
        self.env = None


class _LocationPaths:
    """Store local and remote equivalent paths."""

    def __init__(self, local: str = None, remote: str = None) -> None:
        self.local = local
        self.remote = remote

    def __iter__(self) -> Iterator:
        return iter((self.local, self.remote))


class UnboundRemoteResourceConfig(EntityConfig):
    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption("ssh_cmd", default=ssh_cmd): lambda x: callable(x),
            ConfigOption("copy_cmd", default=copy_cmd): lambda x: callable(x),
            ConfigOption("workspace", default=pwd()): str,
            ConfigOption("workspace_exclude", default=[]): Or(list, None),
            ConfigOption("remote_runpath", default=None): str,
            ConfigOption("testplan_path", default=None): str,
            ConfigOption("remote_workspace", default=None): str,
            ConfigOption("clean_remote", default=False): bool,
            ConfigOption("push", default=[]): Or(list, None),
            ConfigOption("push_exclude", default=[]): Or(list, None),
            ConfigOption("delete_pushed", default=False): bool,
            ConfigOption("fetch_runpath", default=True): bool,
            ConfigOption("fetch_runpath_exclude", default=None): list,
            ConfigOption("pull", default=[]): Or(list, None),
            ConfigOption("pull_exclude", default=[]): Or(list, None),
            ConfigOption("env", default=None): Or(dict, None),
            ConfigOption("setup_script", default=None): Or(list, None),
        }


class RemoteResourceConfig(UnboundRemoteResourceConfig):
    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "remote_host": str,
            ConfigOption("ssh_port", default=22): int,
        }


class RemoteResource(Entity):
    """
    Common base class for Resource that runs on remote host. Handles logistics
    including copy/link workspace and testplan lib to remote, creating runpath
    on remote, and fetching back files from remote etc.

    :param remote_host: Remote hostname to connect to.
    :param ssh_port: The ssh port number of remote host, default is 22.
    :param ssh_cmd: callable that prefix a command with ssh binary and options
    :param copy_cmd: callable that returns the cmdline to do copy on remote host
    :param workspace: Current project workspace to be transferred, default is pwd.
    :param workspace_exclude: Patterns to exclude files when pushing workspace.
    :param remote_runpath: Root runpath on remote host, default is same as local (Linux->Linux)
      or /var/tmp/$USER/testplan/$plan_name (Window->Linux).
    :param testplan_path: Path to import testplan from on remote host,
      default is testplan_lib under remote_runpath
    :param remote_workspace: The path of the workspace on remote host,
      default is fetched_workspace under remote_runpath
    :param clean_remote: Deleted root runpath on remote at exit.
    :param push: Files and directories to push to the remote.
    :param push_exclude: Patterns to exclude files on push stage.
    :param delete_pushed: Deleted pushed files on remote at exit.
    :param fetch_runpath: The flag of fetch remote resource's runpath, default to True.
    :param fetch_runpath_exclude: Exclude files matching PATTERN.
    :param pull: Files and directories to be pulled from the remote at the end.
    :param pull_exclude: Patterns to exclude files on pull stage.
    :param env: Environment variables to be propagated.
    :param setup_script: Script to be executed on remote as very first thing.
    :param status_wait_timeout: remote resource start/stop timeout, default is 60.
    """

    CONFIG = RemoteResourceConfig

    def __init__(
        self,
        remote_host: str,
        ssh_port: int = 22,
        ssh_cmd: Callable = ssh_cmd,
        copy_cmd: Callable = copy_cmd,
        workspace: str = None,
        workspace_exclude: List[str] = None,
        remote_runpath: str = None,
        testplan_path: str = None,
        remote_workspace: str = None,
        clean_remote: bool = False,
        push: List[Union[str, Tuple]] = None,
        push_exclude: List[str] = None,
        delete_pushed: bool = False,
        fetch_runpath: bool = True,
        fetch_runpath_exclude: List[str] = None,
        pull: List[str] = None,
        pull_exclude: List[str] = None,
        env: Dict[str, str] = None,
        setup_script: List[str] = None,
        status_wait_timeout: int = 60,
        **options,
    ) -> None:

        if not worker_is_remote(remote_host):
            raise RuntimeError(
                "Cannot create remote resource on the same host that Testplan runs."
            )
        options.update(self.filter_locals(locals()))
        super(RemoteResource, self).__init__(**options)

        self._remote_plan_runpath = None
        self._remote_resource_runpath = None
        self._child_paths = _LocationPaths()
        self._testplan_import_path = _LocationPaths()
        self._workspace_paths = _LocationPaths()
        self._working_dirs = _LocationPaths()

        self.ssh_cfg = {
            "host": self.cfg.remote_host,
            "port": self.cfg.ssh_port,
        }

        self.setup_metadata = WorkerSetupMetadata()
        self._user = getpass.getuser()
        self.python_binary = (
            os.environ["PYTHON3_REMOTE_BINARY"] if IS_WIN else sys.executable
        )

    def _prepare_remote(self) -> None:

        self._define_remote_dirs()
        self._create_remote_dirs()

        if self.cfg.push:
            self._push_files()

        self.setup_metadata.delete_pushed = self.cfg.delete_pushed
        self.setup_metadata.setup_script = self.cfg.setup_script
        self.setup_metadata.env = self.cfg.env

    def _define_remote_dirs(self) -> None:
        """Define mandatory directories in remote host."""

        self._remote_plan_runpath = self.cfg.remote_runpath or (
            f"/var/tmp/{getpass.getuser()}/testplan/{self._get_plan().cfg.name}"
            if IS_WIN
            else self._get_plan().runpath
        )
        self._workspace_paths.local = fix_home_prefix(
            os.path.abspath(self.cfg.workspace)
        )
        self._workspace_paths.remote = "/".join(
            [self._remote_plan_runpath, "fetched_workspace"]
        )
        self._testplan_import_path.remote = "/".join(
            [self._remote_plan_runpath, "testplan_lib"]
        )
        self._remote_runid_file = os.path.join(
            self._remote_plan_runpath, self._get_plan().runid_filename
        )

        self._remote_resource_runpath = rebase_path(
            self.runpath,
            self._get_plan().runpath,
            self._remote_plan_runpath,
        )
        self.logger.info(
            "%s remote runpath = %s", self, self._remote_resource_runpath
        )
        self._working_dirs.local = pwd()
        self._working_dirs.remote = self._remote_working_dir()
        self.logger.info(
            "%s remote working path = %s", self, self._working_dirs.remote
        )

    def _remote_working_dir(self) -> None:
        """Choose a working directory to use on the remote host."""
        if not is_subdir(
            self._working_dirs.local, self._workspace_paths.local
        ):
            raise RuntimeError(
                f"Current working dir is not within the workspace.\n"
                f"Workspace = {self._workspace_paths.local}\n"
                f"Working dir = {self._working_dirs.local}."
            )

        # Current working directory is within the workspace - use the same
        # path relative to the remote workspace.
        return rebase_path(
            self._working_dirs.local,
            self._workspace_paths.local,
            self._workspace_paths.remote,
        )

    def _create_remote_dirs(self) -> None:
        """Create mandatory directories in remote host."""

        exist_on_remote = self._check_workspace()

        if 0 != self._execute_cmd_remote(
            cmd=filepath_exist_cmd(self._remote_runid_file),
            label="runid file availability check",
            check=False,
        ):
            # clean up remote runpath
            self._execute_cmd_remote(
                cmd=rm_cmd(self._remote_plan_runpath),
                label="remove remote plan runpath",
            )

            self._execute_cmd_remote(
                cmd=mkdir_cmd(self._remote_plan_runpath),
                label="create remote plan runpath",
            )

            self._execute_cmd_remote(
                cmd=f"/bin/touch {self._remote_runid_file}",
                label="create remote runid file",
            )

            self._prepare_workspace(exist_on_remote)
            self._copy_testplan_package()

        self._execute_cmd_remote(
            cmd=mkdir_cmd(self._remote_resource_runpath),
            label="create remote resource runpath",
        )

    def _copy_testplan_package(self) -> None:
        """Make testplan package available on remote host"""

        if self.cfg.testplan_path:
            self._execute_cmd_remote(
                cmd=link_cmd(
                    path=self.cfg.testplan_path,
                    link=self._testplan_import_path.remote,
                ),
                label="linking to testplan package (1).",
            )
            return

        self._testplan_import_path.local = os.path.dirname(
            os.path.dirname(module_abspath(testplan))
        )

        # test if testplan package is available on remote host
        if 0 == self._execute_cmd_remote(
            cmd=filepath_exist_cmd(self._testplan_import_path.local),
            label="testplan package availability check",
            check=False,
        ):
            # exists on remote, make symlink
            self._execute_cmd_remote(
                cmd=link_cmd(
                    path=self._testplan_import_path.local,
                    link=self._testplan_import_path.remote,
                ),
                label="linking to testplan package (2).",
            )

        else:
            # copy to remote
            self._transfer_data(
                # join with "" to add trailing "/" to source
                # this will copy everything under local import path to to testplan_lib
                source=os.path.join(self._testplan_import_path.local, ""),
                target=self._testplan_import_path.remote,
                remote_target=True,
                deref_links=True,
            )

    def _check_workspace(self) -> bool:
        """
        Check if workspace is available on remote host.

        :return: True if exists, false otherwise
        """

        if self.cfg.remote_workspace:
            # User defined the remote workspace to be used
            # will raise if check fail
            if 0 == self._execute_cmd_remote(
                cmd=filepath_exist_cmd(
                    fix_home_prefix(self.cfg.remote_workspace)
                ),
                label="workspace availability check (1)",
                check=True,
            ):
                return True

        if 0 == self._execute_cmd_remote(
            cmd=filepath_exist_cmd(self._workspace_paths.local),
            label="workspace availability check (2)",
            check=False,
        ):
            # local workspace accessible on remote
            return True

        return False

    def _prepare_workspace(self, exist_on_remote: bool) -> None:
        """Make workspace available on remote host."""

        if self.cfg.remote_workspace:
            self.logger.info(
                "%s: user has specified workspace path on remote host, "
                "pointing runpath/fetched_workspace to it",
                self,
            )
            # Make a soft link and return
            self._execute_cmd_remote(
                cmd=link_cmd(
                    path=fix_home_prefix(self.cfg.remote_workspace),
                    link=self._workspace_paths.remote,
                ),
                label="linking to remote workspace (1).",
            )

            return

        if exist_on_remote:
            self.logger.info(
                "%s: local workspace path is accessible on %s, "
                "pointing runpath/fetched_workspace to it",
                self,
                self.ssh_cfg["host"],
            )
            self._execute_cmd_remote(
                cmd=link_cmd(
                    path=self._workspace_paths.local,
                    link=self._workspace_paths.remote,
                ),
                label="linking to remote workspace (2).",
            )

        else:
            # copy to remote
            self.logger.info(
                "%s: local workspace path is inaccessible on %s, "
                "Copying it to remote runpath/fetched_workspace",
                self,
                self.ssh_cfg["host"],
            )
            self._transfer_data(
                # join with "" to add trailing "/" to source
                # this will copy everything under local import path to to testplan_lib
                source=os.path.join(self._workspace_paths.local, ""),
                target=self._workspace_paths.remote,
                remote_target=True,
                exclude=self.cfg.workspace_exclude,
            )
            self.logger.info(
                "%s: creating symlink to imitate local workspace path on %s, "
                "pointing to runpath/fetched_workspace",
                self,
                self.ssh_cfg["host"],
            )
            self._execute_cmd_remote(
                cmd=mkdir_cmd(os.path.dirname(self._workspace_paths.local)),
                label="imitate local workspace path on remote - mkdir",
                check=False,  # just best effort
            )
            self._execute_cmd_remote(
                cmd=link_cmd(
                    path=self._workspace_paths.remote,
                    link=self._workspace_paths.local,
                ),
                label="imitate local workspace path on remote - ln",
                check=False,  # just best effort
            )

    def _push_files(self) -> None:
        """Push files and directories to remote host."""

        # First enumerate the files and directories to be pushed, including
        # both their local source and remote destinations.
        push_files, push_dirs = self._build_push_lists()

        # Add the remote paths to the setup metadata.
        self.setup_metadata.push_files = [path.remote for path in push_files]
        self.setup_metadata.push_dirs = [path.remote for path in push_dirs]

        # Now actually push the files to the remote host.
        self._push_files_to_dst(push_files, push_dirs)

    def _build_push_lists(
        self,
    ) -> Tuple[List[_LocationPaths], List[_LocationPaths]]:
        """
        Create lists of the source and destination paths of files and
        directories to be pushed. Eliminate duplication of sub-directories.

        :return: Tuple containing lists of files and directories to be pushed.
        """
        # Inspect types. Push config may either be a list of string paths, e.g:
        # ['/path/to/file1', '/path/to/file1']
        #
        # Or it may be a list of tuples where the destination for each source
        # is specified also:
        # [('/local/path/to/file1', '/remote/path/to/file1'),
        #  ('/local/path/to/file2', '/remote/path/to/file2')]

        if not all(
            isinstance(entry, str) or len(entry) == 2
            for entry in self.cfg.push
        ):
            raise TypeError(
                "The push param takes a list of str or (src, dst) tuple"
            )

        push_locations = self._build_push_dests(self.cfg.push)

        # Now seperate the push sources into lists of files and directories.
        push_files = []
        push_dirs = []

        for source, dest in push_locations:
            source = source.rstrip(os.sep)
            if os.path.isfile(source):
                push_files.append(_LocationPaths(source, dest))
            elif os.path.isdir(source):
                push_dirs.append(
                    _LocationPaths(os.path.join(source, ""), dest)
                )
            else:
                self.logger.error(
                    '%s: item "%s" cannot be pushed!',
                    self,
                    source,
                )

        # Eliminate push duplications
        if push_dirs and len(push_dirs) > 1:
            push_dirs.sort(key=lambda x: x.local)
            for idx in range(len(push_dirs) - 1):
                if push_dirs[idx + 1].local.startswith(push_dirs[idx].local):
                    push_dirs[idx] = None
            push_dirs = [_dir for _dir in push_dirs if _dir is not None]

        return push_files, push_dirs

    def _build_push_dests(
        self, push_sources: Union[List[str], List[Tuple[str, str]]]
    ) -> Union[List[str], List[Tuple[str, str]]]:
        """
        When the destination paths have not been explicitly specified, build
        them automatically. If an absolute path is given on Linux, we will push
        to the same path on remote. If on Windows or a relative path is given on
        Linux, we will push to the save relative path in respect to working
        directory.

        """
        push_locations = []

        if IS_WIN:
            for entry in push_sources:
                if isinstance(entry, str):
                    src = entry
                    dst = rebase_path(
                        src,
                        self._working_dirs.local,
                        self._working_dirs.remote,
                    )

                else:
                    src, dst = entry
                    if not os.path.isabs(dst):
                        dst = rebase_path(
                            dst,
                            self._working_dirs.local,
                            self._working_dirs.remote,
                        )

                push_locations.append((src, dst))

        else:
            for entry in push_sources:
                if isinstance(entry, str):
                    src = entry
                    if os.path.isabs(src):
                        dst = src
                    else:
                        dst = os.path.join(self._working_dirs.remote, src)
                else:
                    src, dst = entry
                    if not os.path.isabs(dst):
                        dst = os.path.join(
                            self._working_dirs.remote,
                            os.path.relpath(dst, self._working_dirs.local),
                        )

                push_locations.append((src, dst))

        return push_locations

    def _push_files_to_dst(self, push_files: List, push_dirs: List) -> None:
        """
        Push files and directories to the remote host. Both the source and
        destination paths should be specified.

        :param push_files: Files to push.
        :param push_dirs:  Directories to push.
        """
        for source, dest in itertools.chain(push_files, push_dirs):
            remote_dir = dest.rpartition("/")[0]
            self.logger.debug("%s create remote dir: %s", self, remote_dir)
            self._execute_cmd_remote(
                cmd=mkdir_cmd(remote_dir), label="create remote dir"
            )
            self._transfer_data(
                source=source,
                target=dest,
                remote_target=True,
                exclude=self.cfg.push_exclude,
            )

    def _fetch_results(self) -> None:
        """Fetch back to local host the results generated remotely."""
        if not self.cfg.fetch_runpath:
            self.logger.debug(
                "Skip fetch results stage - %s", self.ssh_cfg["host"]
            )
            return
        self.logger.debug("Fetch results stage - %s", self.ssh_cfg["host"])
        try:
            self._transfer_data(
                source=self._remote_resource_runpath,
                remote_source=True,
                target=self.parent.runpath,
                exclude=self.cfg.fetch_runpath_exclude,
            )
            if self.cfg.pull:
                self._pull_files()
        except Exception as exc:
            self.logger.debug(
                "While fetching result from worker [%s]: %s", self, exc
            )

    def _clean_remote(self) -> None:
        if self.cfg.clean_remote:
            self.logger.debug(
                "Clean root runpath on remote host - %s", self.ssh_cfg["host"]
            )

            self._execute_cmd_remote(
                cmd=f"/bin/rm -rf {self._remote_plan_runpath}",
                label="Clean remote root runpath",
            )

    def _pull_files(self) -> None:
        """Pull custom files from remote host."""

        pull_dst = os.path.join(self.runpath, "pulled_files")
        makedirs(pull_dst)

        for entry in self.cfg.pull:
            try:
                self._transfer_data(
                    source=entry,
                    remote_source=True,
                    target=pull_dst,
                    exclude=self.cfg.pull_exclude,
                )
            except Exception as exc:
                self.logger.debug(
                    "While fetching result from worker [%s]: %s", self, exc
                )

    def _remote_sys_path(self) -> List[str]:

        sys_path = [self._testplan_import_path.remote]

        for path in sys.path:
            path = fix_home_prefix(path)

            if is_subdir(path, self._workspace_paths.local):
                path = rebase_path(
                    path,
                    self._workspace_paths.local,
                    self._workspace_paths.remote,
                )

            sys_path.append(path)

        return sys_path

    def _get_plan(self):
        """traverse upwards to find TestRunner"""

        parent = getattr(self, "parent", None)
        while parent:
            if isinstance(parent, testplan.runnable.TestRunner):
                return parent
            else:
                parent = getattr(parent, "parent", None)

    def _execute_cmd_remote(
        self,
        cmd,
        label=None,
        check=True,
        stdout=None,
        stderr=None,
        detailed_log: LogDetailsOption = LogDetailsOption.LOG_ON_ERROR,
    ):
        """
        Execute a command on the remote host.

        :param cmd: Remote command to execute - list of parameters.
        :param label: Optional label for debugging.
        :param check: Whether to check command return-code - defaults to True.
                      See self._execute_cmd for more detail.
        """
        return execute_cmd(
            self.cfg.ssh_cmd(self.ssh_cfg, cmd),
            label=label,
            check=check,
            logger=self.logger,
            stdout=stdout,
            stderr=stderr,
            detailed_log=detailed_log,
        )

    def _remote_copy_path(self, path):
        """
        Return a path on the remote host in the format user@host:path,
        suitable for use in a copy command such as `scp`.
        """
        return "{user}@{host}:{path}".format(
            user=self._user, host=self.ssh_cfg["host"], path=path
        )

    def _transfer_data(
        self,
        source,
        target,
        remote_source=False,
        remote_target=False,
        **copy_args,
    ):
        if remote_source:
            source = self._remote_copy_path(source)
        if remote_target:
            target = self._remote_copy_path(target)
        self.logger.debug("Copying %(source)s to %(target)s", locals())
        cmd = self.cfg.copy_cmd(
            source, target, port=self.ssh_cfg["port"], **copy_args
        )
        with open(os.devnull, "w") as devnull:
            execute_cmd(
                cmd,
                "transfer data [..{}]".format(os.path.basename(target)),
                stdout=devnull,
                logger=self.logger,
            )
