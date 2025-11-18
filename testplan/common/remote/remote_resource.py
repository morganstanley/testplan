import getpass
import os
import re
import sys
from collections.abc import Iterable, Iterator
from functools import partial
from typing import Callable, Dict, List, Optional, Tuple, Union, cast

from schema import And, Or

import testplan
import testplan.runnable
from testplan.common.config import ConfigOption
from testplan.common.entity import Entity, EntityConfig
from testplan.common.remote.remote_runtime import (
    RuntimeBuilder,
    SourceTransferBuilder,
)
from testplan.common.remote.ssh_client import SSHClient
from testplan.common.utils.path import (
    fix_home_prefix,
    is_subdir,
    makedirs,
    module_abspath,
    pwd,
    rebase_path,
)
from testplan.common.utils.process import (
    execute_cmd,
)
from testplan.common.utils.remote import (
    IS_WIN,
    copy_cmd,
    filepath_exist_cmd,
    link_cmd,
    mkdir_cmd,
    rm_cmd,
    ssh_cmd,  # deprecated
    worker_is_remote,
)


class WorkerSetupMetadata:
    """
    Metadata used on worker setup stage execution.
    Pushed dirs and files will be registered for deletion at exit.
    """

    def __init__(self) -> None:
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
            ConfigOption("remote_workspace", default=None): str,
            # proposing cfg clobber_remote_workspace,
            # to overwrite what's in remote_workspace when set to True
            ConfigOption("clean_remote", default=False): bool,
            ConfigOption("push", default=[]): Or(
                And(
                    list,
                    lambda x: all(
                        map(lambda y: isinstance(y, str) or len(y) == 2, x)
                    ),
                ),
                None,
            ),
            ConfigOption("push_exclude", default=[]): Or(list, None),
            ConfigOption("delete_pushed", default=False): bool,
            ConfigOption("fetch_runpath", default=True): bool,
            ConfigOption("fetch_runpath_exclude", default=None): list,
            ConfigOption("pull", default=[]): Or(list, None),
            ConfigOption("pull_exclude", default=[]): Or(list, None),
            ConfigOption("env", default=None): Or(dict, None),
            ConfigOption("setup_script", default=None): Or(list, None),
            ConfigOption("paramiko_config", default=None): Or(dict, None),
            ConfigOption("remote_runtime_builder", default=None): Or(
                lambda x: isinstance(x, RuntimeBuilder), None
            ),
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
    :param paramiko_config: Paramiko SSH client extra configuration.
    :param remote_runtime_builder: RuntimeBuilder instance to prepare remote python env.
        Default is ``SourceTransferBuilder()``.
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
        paramiko_config: Optional[dict] = None,
        remote_runtime_builder: Optional[RuntimeBuilder] = None,
        status_wait_timeout: int = 60,
        **options,
    ) -> None:
        if not worker_is_remote(remote_host):
            # TODO: allow connecting to local for testing purpose?
            raise RuntimeError(
                "Cannot create remote resource on the same host that Testplan runs."
            )
        options.update(self.filter_locals(locals()))
        super(RemoteResource, self).__init__(**options)

        self.setup_metadata = WorkerSetupMetadata()
        self._user = getpass.getuser()

        self.ssh_cfg = {
            "host": self.cfg.remote_host,
            "port": self.cfg.ssh_port,
        }
        # if 0 != self._execute_cmd_remote("uname"):
        #     raise NotImplementedError(
        #         "RemoteResource not supported on Windows remote hosts."
        #     )

        self._remote_plan_runpath: str
        self._remote_resource_runpath: str
        self._child_paths = _LocationPaths()
        self._testplan_import_path = _LocationPaths()
        self._testplan_import_path.local = os.path.dirname(
            os.path.dirname(module_abspath(testplan))
        )
        self._workspace_paths = _LocationPaths()
        self._working_dirs = _LocationPaths()

        self._error_exec = []

        # remote file system obj outside runpath that needs to be cleaned upon
        # exit when clean_remote is True, otherwise it will break workspace
        # detect etc. in next run
        self._dangling_remote_fs_obj = (
            None  # TODO: merge into _pushed_remote_paths
        )

        # Initialize SSHClient instance for managing SSH connections
        extra_paramiko_cfg = self.cfg.paramiko_config or {}
        self._ssh_client = SSHClient(
            self.cfg.remote_host, self.cfg.ssh_port, **extra_paramiko_cfg
        )

        # used in subclasses, see remote_python_bin
        self._remote_pybin = None
        self._remote_runtime_builder: RuntimeBuilder = (
            self.cfg.remote_runtime_builder or SourceTransferBuilder()
        )

        self._pushed_remote_paths = []

    @property
    def error_exec(self) -> list:
        return self._error_exec

    @property
    def remote_python_bin(self) -> str:
        if self._remote_pybin is None:
            raise RuntimeError(
                f"{self}: remote python binary not set properly."
            )
        return self._remote_pybin

    def _prepare_remote(self) -> None:
        self._check_remote_os()

        self._define_remote_dirs()
        self._create_remote_dirs()

        if self.cfg.push:
            self._push_files(self.cfg.push, self.cfg.push_exclude)

        self.setup_metadata.setup_script = self.cfg.setup_script
        self.setup_metadata.env = self.cfg.env

    def _define_remote_dirs(self) -> None:
        """Define mandatory directories in remote host."""
        plan_runpath = cast(str, self._get_plan().runpath)

        self._remote_plan_runpath = self.cfg.remote_runpath or (
            f"/var/tmp/{getpass.getuser()}/testplan/{self._get_plan().cfg.name}"
            if IS_WIN
            else plan_runpath
        )
        self._workspace_paths.local = fix_home_prefix(
            os.path.abspath(self.cfg.workspace)
        )
        self._workspace_paths.remote = "/".join(
            [self._remote_plan_runpath, "fetched_workspace"]
        )
        self._remote_runid_file = os.path.join(
            self._remote_plan_runpath, self._get_plan().runid_filename
        )

        self._remote_resource_runpath = rebase_path(
            self.runpath,
            plan_runpath,
            self._remote_plan_runpath,
        )
        self.logger.info(
            "%s: remote runpath = %s", self, self._remote_resource_runpath
        )
        self._working_dirs.local = pwd()
        self._working_dirs.remote = self._remote_working_dir()
        self.logger.info(
            "%s: remote working path = %s", self, self._working_dirs.remote
        )

        # here we apply checks for corner cases:
        # NOTE: if remote runpath under local workspace,
        # NOTE: it would fail to imitate local dir structure in curr impl
        if self._workspace_paths.local.startswith(self._remote_plan_runpath):
            # why?: possible name clash, e.g. 'venv'
            raise RuntimeError(
                f"Local workspace '{self._workspace_paths.local}' cannot be "
                f"subdirectory of remote runpath '{self._remote_plan_runpath}'."
            )

    def _remote_working_dir(self) -> str:
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

        if (
            0
            != self._ssh_client.exec_command(
                cmd=filepath_exist_cmd(self._remote_runid_file),
                label="runid file availability check",
                check=False,
            )[0]
        ):
            # clean up remote runpath
            self._ssh_client.exec_command(
                cmd=rm_cmd(self._remote_plan_runpath),
                label="remove remote plan runpath possibly from previous run",
            )

            exist_on_remote = self._check_workspace()

            # NOTE: should record created dirs from mkdir -p
            self._ssh_client.exec_command(
                cmd=mkdir_cmd(self._remote_plan_runpath),
                label="create remote plan runpath",
            )

            self._ssh_client.exec_command(
                cmd=f"/bin/touch {self._remote_runid_file}",
                label="create remote runid file",
            )

            # corner cases:
            # - local workspace under remote runpath
            # more?
            self._prepare_workspace(exist_on_remote)
            self._setup_remote_pyenv()

        self._ssh_client.exec_command(
            cmd=mkdir_cmd(self._remote_resource_runpath),
            label="create remote resource runpath",
        )

    def _setup_remote_pyenv(self):
        """
        setup remote python runtime environment with RuntimeBuilder
        """

        self._remote_runtime_builder.bootstrap(
            local_runpath=self.runpath,
            remote_runpath=self._remote_plan_runpath,
            local_cmd_exec=partial(
                execute_cmd, logger=self._remote_runtime_builder.logger
            ),
            remote_cmd_exec=self._ssh_client.exec_command,
            parent_cfg=self.cfg,
        )
        self._remote_pybin = (
            self._remote_runtime_builder.remote_prepare_pybin()
        )
        self.logger.info(
            "%s: picking remote python %s", self, self._remote_pybin
        )
        self._log_remote_python_ver(self._remote_pybin)
        paths_to_transfer = self._remote_runtime_builder.local_export_pyenv()
        remote_paths = self._push_files_to_dst(
            paths_to_transfer,
            self._remote_runtime_builder.cfg.transfer_exclude,
            deref_links=True,
            as_is=True,
        )
        self._testplan_import_path.remote = (
            self._remote_runtime_builder.remote_setup_pyenv(remote_paths)
        )

    def _log_remote_python_ver(self, remote_python_bin: str):
        _, stdout, _ = self._ssh_client.exec_command(
            cmd=f'{remote_python_bin} -c "import sys; print(tuple(sys.version_info))"',
            label="detect remote python version",
        )
        _m = re.match(
            r"^\((\d), (\d+), (\d+), '(\w+)', (\d+)\)$", stdout.strip()
        )
        remote_python_ver = (
            (
                int(_m.group(1)),
                int(_m.group(2)),
                int(_m.group(3)),
                _m.group(4),
                int(_m.group(5)),
            )
            if _m
            else None
        )

        self.logger.info(
            "%s: remote python version %s; local python version %s",
            self,
            remote_python_ver,
            tuple(sys.version_info),
        )

    def _check_workspace(self) -> bool:
        """
        Check if workspace is available on remote host.

        :return: True if exists, false otherwise
        """

        if self.cfg.remote_workspace:
            # User defined the remote workspace to be used
            # will raise if check fail
            if (
                0
                == self._ssh_client.exec_command(
                    cmd=filepath_exist_cmd(
                        fix_home_prefix(self.cfg.remote_workspace)
                    ),
                    label="workspace availability check (1)",
                    check=True,
                )[0]
            ):
                return True

        if (
            0
            == self._ssh_client.exec_command(
                cmd=filepath_exist_cmd(self._workspace_paths.local),
                label="workspace availability check (2)",
                check=False,
            )[0]
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
            self._ssh_client.exec_command(
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
            # proposed: if clobber_remote_workspace set, overwrite remote
            self._ssh_client.exec_command(
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
                # this will copy everything under local workspace path to fetched_workspace
                source=os.path.join(self._workspace_paths.local, ""),
                target=self._workspace_paths.remote,
                remote_target=True,
                exclude=self.cfg.workspace_exclude,
            )

            if IS_WIN:
                return

            self.logger.info(
                "%s: creating symlink to imitate local workspace path on %s, "
                "pointing to runpath/fetched_workspace",
                self,
                self.ssh_cfg["host"],
            )
            rmt_non_existing = None
            # TODO: uncomment later
            # TODO: there is another issue related to created dir cleanup
            # TODO: if push given, pushed files under created dir and delete_pushed
            # TODO: set to False, what to do?
            # r, w = os.pipe()
            # if 0 == self._execute_cmd_remote(
            #     cmd="/bin/bash -c "
            #     + shlex.quote(
            #         'e=""; for i in '
            #         + " ".join(
            #             map(
            #                 shlex.quote,
            #                 self._workspace_paths.local.split(os.sep)[1:],
            #             )
            #         )
            #         + '; do e+="/${i}"; if [ ! -e "$e" ]; then echo "$e"; break; fi; done'
            #     ),
            #     label="imitate local workspace path on remote - detect non-existing",
            #     stdout=os.fdopen(w),
            #     check=False,  # XXX: bash might not be there
            # ):
            #     rmt_non_existing = os.fdopen(r).read().strip() or None
            if (
                0
                == self._ssh_client.exec_command(
                    cmd=mkdir_cmd(
                        os.path.dirname(self._workspace_paths.local)
                    ),
                    label="imitate local workspace path on remote - mkdir",
                    check=False,  # just best effort
                )[0]
                and 0
                == self._ssh_client.exec_command(
                    cmd=link_cmd(
                        path=self._workspace_paths.remote,
                        link=self._workspace_paths.local,
                    ),
                    label="imitate local workspace path on remote - ln",
                    check=False,  # just best effort
                )[0]
            ):
                # NOTE: we shall always remove created symlink
                self._dangling_remote_fs_obj = (
                    rmt_non_existing or self._workspace_paths.local
                )
                self.logger.info(
                    "%s: on %s, %s and its possible descendants are "
                    "created to imitate local workspace path",
                    self,
                    self.ssh_cfg["host"],
                    self._dangling_remote_fs_obj,
                )

    def _push_files(self, paths, exclude_patterns=None):
        """Push files and directories to remote host."""

        # First enumerate the paths to be pushed, including
        # both their local source and remote destinations.
        push_pairs = self._build_push_lists(paths)

        self._pushed_remote_paths.extend([path.remote for path in push_pairs])

        # Now actually push the files to the remote host.
        return self._push_files_to_dst(push_pairs, exclude_patterns)

    def _build_push_lists(self, push_sources) -> List[_LocationPaths]:
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

        push_locations = self._build_push_dests(push_sources)

        # Now seperate the push sources into lists of files and directories.
        push_files = []
        push_dirs = []

        for source, dest in push_locations:
            if os.path.isfile(source):
                push_files.append(_LocationPaths(source, dest))
            elif os.path.isdir(source):
                # ensure src trailing os.sep, dst no trailing os.sep
                push_dirs.append(
                    _LocationPaths(
                        source.rstrip(os.sep) + os.sep, dest.rstrip(os.sep)
                    )
                )
            else:
                self.logger.error(
                    '%s: item "%s" cannot be pushed!',
                    self,
                    source,
                )

        # TODO: eliminate push duplications, remote matters

        return push_files + push_dirs

    def _build_push_dests(
        self, push_sources: Union[List[str], List[Tuple[str, str]]]
    ) -> List[Tuple[str, str]]:
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

    def _push_files_to_dst(
        self,
        loc_paths: Iterable[Union[_LocationPaths, tuple[str, str]]],
        exclude: Optional[list[str]],
        **copy_args,
    ) -> list[str]:
        """
        Push files and directories to the remote host. Both the source and
        destination paths should be specified.

        TODO: record created dirs
        NOTE: input paths should have trailing os.sep removed
        """
        remotes = []
        for source, dest in loc_paths:
            remote_dir = dest.rpartition("/")[0]
            self.logger.debug("%s create remote dir: %s", self, remote_dir)
            self._ssh_client.exec_command(
                cmd=mkdir_cmd(remote_dir), label="create remote dir"
            )
            self._transfer_data(
                source=source,
                target=dest,
                remote_target=True,
                exclude=exclude,
                **copy_args,
            )
            remotes.append(dest)
        return list(set(remotes))

    def _fetch_results(self) -> None:
        """Fetch back to local host the results generated remotely."""
        if not self.cfg.fetch_runpath:
            self.logger.debug(
                "Skip fetch results stage - %s", self.ssh_cfg["host"]
            )
            return
        if not hasattr(self, "_remote_resource_runpath"):
            self.logger.error(
                "%s not properly set up, skip fetch results stage", self
            )
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
            self._error_exec.append(exc)
            self.logger.warning(
                "While fetching result from remote resource [%s]: %s",
                self,
                exc,
            )

    def _clean_remote(self) -> None:
        if self.cfg.clean_remote:
            self.logger.user_info(
                "Clean root runpath on remote host - %s", self.ssh_cfg["host"]
            )

            self._ssh_client.exec_command(
                cmd=rm_cmd(self._remote_plan_runpath),
                label="Clean remote root runpath",
            )

            if self._dangling_remote_fs_obj:
                self._ssh_client.exec_command(
                    cmd=rm_cmd(self._dangling_remote_fs_obj),
                    label=f"Remove imitated workspace outside runpath",
                )
                self._dangling_remote_fs_obj = None

            self._remote_runtime_builder.remote_teardown_pyenv()

        if self.cfg.delete_pushed:
            self._ssh_client.exec_command(
                cmd=["/bin/rm", "-rf"] + self._pushed_remote_paths,
                label="Delete pushed files as requested",
            )

        self._ssh_client.close()

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
                self._error_exec.append(exc)
                self.logger.warning(
                    "While fetching result from remote resource [%s]: %s",
                    self,
                    exc,
                )

    def _remote_sys_path(self) -> List[str]:
        sys_path = [self._testplan_import_path.remote]

        for path in sys.path:
            if path.startswith(sys.base_prefix):
                # remote python ver could be different, skip stdlib
                continue

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
        raise RuntimeError(
            "impossible: no TestRunner ancestor, caller side bug"
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
                "transfer data [..{}]".format(os.path.basename(source)),
                stdout=devnull,
                logger=self.logger,
            )

    def _check_remote_os(self):
        if "REMOTE_OS" not in os.environ:
            _, stdout, _ = self._ssh_client.exec_command(
                cmd="cat /etc/os-release",
                label="Check remote OS",
                check=False,
            )

            # for efficiency, we assume all remote resources are of same os
            self.logger.debug("Setting REMOTE_OS = %s", stdout)
            os.environ["REMOTE_OS"] = stdout
