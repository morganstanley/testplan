"""
python runtime environment builder for remote test execution

pybin refers to the path to python binary
pyenv refers to the python environment, e.g. venv or system env

XXX: support pathlib
"""

import os.path
import shlex
import sys
from abc import ABC, abstractmethod
from typing import Callable

from schema import Or, And
from typing_extensions import TypeAlias  # available in Python 3.10+

from testplan.common.config import Config, ConfigOption
from testplan.common.entity import Entity
from testplan.common.utils.path import module_abspath
from testplan.common.utils.remote import (
    filepath_exist_cmd,
    link_cmd,
    rm_cmd,
    mkdir_cmd,
)

CmdExecF: TypeAlias = Callable[..., tuple[int, str, str]]


OVERRIDDEN_PYTHON_BIN = "REMOTE_PYTHON3_BINARY"


class RuntimeBuilder(Entity, ABC):
    """
    common parent abstract class for remote python runtime environment builder

    methods prefixed with "remote_" are executed on remote
    methods prefixed with "local_" are executed on local
    """

    def __init__(self, **options):
        """
        common constructor for config setting only
        """
        super().__init__(**options)
        self._l_runpath: str
        self._r_runpath: str
        self._lcmd_exec: CmdExecF
        self._rcmd_exec: CmdExecF

    def bootstrap(
        self,
        local_runpath: str,
        remote_runpath: str,
        local_cmd_exec: CmdExecF,
        remote_cmd_exec: CmdExecF,
        parent_cfg: Config,  # TestRunnerConfig
    ):
        """
        runtime initialization with info from parent ``RemoteResource``
        """
        self._l_runpath = local_runpath
        self._r_runpath = remote_runpath
        self._lcmd_exec = local_cmd_exec
        self._rcmd_exec = remote_cmd_exec
        self.cfg.parent = parent_cfg

    @abstractmethod
    def remote_prepare_pybin(self) -> str:
        """
        prepare pybin on remote side

        :return: python binary path on remote to be used to execute tests
        """

    @abstractmethod
    def local_export_pyenv(self) -> list[tuple[str, str]]:
        """
        export pyenv on local side, return a list of ``(local_path, remote_path)``
        pairs that need to be transferred to remote side
        """

    @abstractmethod
    def remote_setup_pyenv(
        self,
        remote_paths: list[str],
    ) -> str:
        """
        setup pyenv on remote side

        :param remote_paths: list of paths on remote that are transferred from
            local
        :return: path to testplan parent dir on remote, for ``sys.path``
            alteration
        """
        # NOTE: since syspath alteration on remote cannot be merged into
        # NOTE: builder now, this method cannot return None

    @abstractmethod
    def remote_teardown_pyenv(self):
        """
        teardown pyenv on remote side
        """

    @abstractmethod
    def get_remote_rpyc_bin(self) -> str:
        """
        return rpyc binary path on remote side
        """


class RuntimeBuilderConfig(Config):
    """
    common base class for config of runtime builders
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("transfer_exclude", default=[]): Or(
                And(list, lambda x: all(isinstance(i, str) for i in x)), None
            ),
        }


class PipBasedBuilderConfig(RuntimeBuilderConfig):
    """
    config class for :py:class:`PipBasedBuilder`
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("python_base_bin", default="python3"): str,
            # NOTE: validation postponed to py detect
            ConfigOption("venv_path", default=None): str,
            ConfigOption("reuse_venv_if_exist", default=False): bool,
            ConfigOption("skip_install_deps_if_exist", default=False): bool,
            ConfigOption("use_sys_env", default=False): bool,
            ConfigOption("extra_install_env_vars", default=None): dict,
            ConfigOption("overridden_deps", default=None): And(
                list, lambda x: all(isinstance(i, str) for i in x)
            ),
            # internal option, venv path under runpath on remote
            ConfigOption("_runpath_venv_path", default="venv"): str,
            # internal option, local packages dir under runpath on remote
            # here "local" refers to packages installed from local paths,
            # opposite to "upstream" from package index
            ConfigOption(
                "_runpath_local_package_dir", default="local_packages"
            ): str,
        }


class PipBasedBuilder(RuntimeBuilder):
    """
    pip-based remote python runtime environment builder, which would install
    the exact same packages as local on remote machine using pip-compatible
    interface provided by the ``uv`` python package tool

    :param transfer_exclude: list of glob patterns to exclude from transfer
        during remote runtime environment building
    :param python_base_bin: python base binary to create venv from or use
        directly on remote
    :param venv_path: user-specified full venv path on remote
    :param reuse_venv_if_exist: if ``venv_path`` specified and exists, reuse
        it without deletion and re-creation, while packages still uploaded
        and installed
    :param skip_install_deps_if_exist: if ``venv_path`` specified and exists,
        skip packages installation, useful if packages already installed in
        venv and no dependency changed since last run. note no dependency
        check is performed, use with caution.
    :param use_sys_env: use system python environment directly without venv
        creation
    :param extra_install_env_vars: dict of extra environment variables to set
        during ``uv pip install`` on remote
    :param overridden_deps: list of package requirement strings to override
        (replace) the dependencies detected from local venv, should be alike
        the format of ``uv pip freeze`` output, e.g.
        ``["packageA==1.2.3", "packageB @ file:///path/to/packageB",
        "packageC", "packageA!=1.2.3+local", ...]``
    """

    CONFIG = PipBasedBuilderConfig

    def __init__(self, **options):
        super().__init__(**options)
        self._upstream_pkgs: list[str]
        self._local_pkgs: list[str]  # local from the perspective of remote
        self._remote_python_bin: str
        self._skip_install_deps = False

    @staticmethod
    def group_freezed(packages: list):
        # NOTE: impl relies on behaviour of "uv pip freeze"
        upstream = []
        local = []
        for p in packages:
            # "uv pip freeze"-exported editable must be local dirs
            # ``pip install -e git://...`` will create ``src`` under ``sys.prefix``
            if p.startswith("-e file://"):
                local.append(p[10:])
            elif " @ " in p:
                # TODO: are svn/hg/... still valid?
                p_ = p.split(" @ ")[1]
                if p_.startswith("file://"):
                    local.append(p_[7:])
                else:
                    # assuming package index reachable from remote
                    upstream.append(p_)
            else:
                upstream.append(p)

        return upstream, local

    @staticmethod
    def deduce_python_bin(env_prefix: str) -> str:
        # TODO: windows
        return os.path.join(env_prefix, "bin", "python3")

    def bootstrap(self, *args, **kwargs):
        super().bootstrap(*args, **kwargs)
        if env_python_bin := os.environ.get(OVERRIDDEN_PYTHON_BIN):
            self.cfg.set_local("python_base_bin", env_python_bin)

    def remote_prepare_pybin(self) -> str:
        remote_base_bin = self.cfg.python_base_bin

        if self.cfg.use_sys_env:
            self._remote_python_bin = remote_base_bin
            return remote_base_bin

        if self.cfg.venv_path:
            if (
                self._rcmd_exec(
                    filepath_exist_cmd(self.cfg.venv_path),
                    label="test if venv_path exists",
                    check=False,
                )[0]
                == 0
            ):
                if self.cfg.reuse_venv_if_exist:
                    self._remote_python_bin = self.deduce_python_bin(
                        self.cfg.venv_path
                    )
                    self._skip_install_deps = (
                        self.cfg.skip_install_deps_if_exist
                    )
                    return self._remote_python_bin
                self._rcmd_exec(
                    rm_cmd(self.cfg.venv_path),
                    label="remove existing venv_path on remote",
                )
            else:
                self._rcmd_exec(
                    mkdir_cmd(self.cfg.venv_path),
                    label="create empty directory of venv_path on remote",
                )
            venv_path = self.cfg.venv_path
        else:
            venv_path = os.path.join(
                self._r_runpath, self.cfg._runpath_venv_path
            )

        self._rcmd_exec(
            [
                remote_base_bin,
                "-m",
                "venv",
                venv_path,
            ],
            label="create remote venv",
        )
        self._remote_python_bin = self.deduce_python_bin(venv_path)
        return self._remote_python_bin

    def local_export_pyenv(self):
        if self.cfg.overridden_deps:
            # NOTE: here we don't perform any check upon user input
            self._upstream_pkgs, local_paths = self.group_freezed(
                self.cfg.overridden_deps
            )
        else:
            import uv  # so that usage of uv noticed by linter

            _, stdout, _ = self._lcmd_exec(
                [sys.executable, "-m", uv.__name__, "pip", "freeze"],
                label="execute uv pip freeze on local",
            )
            self._upstream_pkgs, local_paths = self.group_freezed(
                stdout.splitlines()
            )
        self.logger.info("local packages to transfer: %s", local_paths)
        self._local_pkgs = [
            os.path.join(
                self._r_runpath,
                self.cfg._runpath_local_package_dir,
                x.rsplit(os.sep, 1)[1],
            )
            for x in local_paths
        ]
        return list(
            map(
                lambda x: (
                    x,
                    os.path.join(
                        self._r_runpath,
                        self.cfg._runpath_local_package_dir,
                        "",  # (explicitly) force creation of parent package dir
                    ),
                ),
                local_paths,
            )
        )

    def remote_setup_pyenv(self, remote_paths):
        import uv

        if not self._skip_install_deps:
            self._rcmd_exec(
                [self._remote_python_bin, "-m", "pip", "install", uv.__name__],
                label="install uv on remote",
            )
            local_pkgs_pattern = (
                shlex.quote(
                    os.path.join(
                        self._r_runpath, self.cfg._runpath_local_package_dir
                    )
                )
                + os.sep
                + "*"
            )
            # NOTE: is it necessary to add self._upstream_pkgs to requirements.txt?
            # NOTE: we need a glob here given possible multiple local
            # NOTE: packages. since shlex.quote only applied on list, we pass a
            # NOTE: string
            self._rcmd_exec(
                shlex.join(
                    [
                        self._remote_python_bin,
                        "-m",
                        uv.__name__,
                        "pip",
                        "install",
                        *self._upstream_pkgs,
                    ]
                )
                + " "
                + local_pkgs_pattern,
                label="install packages on remote",
                env=self.cfg.extra_install_env_vars or None,
            )
        _, r_testplan_parent, _ = self._rcmd_exec(
            [
                self._remote_python_bin,
                "-c",
                "import testplan, os.path; "
                "print(os.path.dirname("
                "os.path.dirname(testplan.__file__)), end='')",
            ],
            label="get remote testplan parent dir",
        )
        return r_testplan_parent

    def remote_teardown_pyenv(self):
        # everything under runpath, should be auto removed
        pass

    def get_remote_rpyc_bin(self) -> str:
        return os.path.join(
            os.path.dirname(self._remote_python_bin),
            "rpyc_classic.py",
        )


class SourceTransferBuilderConfig(RuntimeBuilderConfig):
    """
    config class for :py:class:`SimpleSyspathBuilder`
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("python_bin", default=sys.executable): str,
            ConfigOption("existing_testplan_parent", default=None): str,
            ConfigOption("_runpath_testplan_dir", default="testplan_lib"): str,
        }


class SourceTransferBuilder(RuntimeBuilder):
    """
    source-code-based remote python runtime environment builder, which would
    only transfer testplan source code to remote or reuse existing testplan
    source path on remote specified by user. certain ``sys.path`` manipulation
    should be performed by caller/children classes of ``RemoteResource``
    accordingly.

    :param transfer_exclude: list of glob patterns to exclude from transfer
    :param python_bin: python binary to use on remote
    :param existing_testplan_parent: user-specified existing testplan parent
        directory on remote, if specified local testplan source code would not
        be transferred to remote
    """

    CONFIG = SourceTransferBuilderConfig

    def __init__(self, **options):
        super().__init__(**options)
        self._l_testplan_ppath: str
        self._r_testplan_ppath: str

    def bootstrap(self, *args, **kwargs):
        super().bootstrap(*args, **kwargs)
        if env_python_bin := os.environ.get(OVERRIDDEN_PYTHON_BIN):
            self.cfg.set_local("python_bin", env_python_bin)

        import testplan

        self._l_testplan_ppath = os.path.dirname(
            os.path.dirname(module_abspath(testplan))
        )
        self._r_testplan_ppath = os.path.join(
            self._r_runpath, self.cfg._runpath_testplan_dir
        )

    def remote_prepare_pybin(self) -> str:
        return self.cfg.python_bin

    def local_export_pyenv(self) -> list:
        if self.cfg.existing_testplan_parent:
            # remote path specified, no need to transfer files
            return []

        # NOTE: this is obviously a quite rough test
        if (
            self._rcmd_exec(
                filepath_exist_cmd(
                    os.path.join(self._l_testplan_ppath, "testplan", "base.py")
                ),
                label="test if testplan accessible on remote",
                check=False,
            )[0]
            == 0
        ):
            # local path accessible on remote, no need to transfer files
            return []
        # indicate transfer of local testplan path to remote
        return [
            (
                os.path.join(self._l_testplan_ppath, ""),
                self._r_testplan_ppath,
            )
        ]

    def remote_setup_pyenv(self, remote_paths):
        if self.cfg.existing_testplan_parent:
            remote_src = self.cfg.existing_testplan_parent
            self._rcmd_exec(
                link_cmd(remote_src, self._r_testplan_ppath),
                label=f"link user-specified testplan path {remote_src} to "
                f"{self.cfg._runpath_testplan_dir} under runpath",
            )
        elif remote_paths:
            remote_src = self._r_testplan_ppath
            # no need to make symlink
        else:
            remote_src = self._l_testplan_ppath
            self._rcmd_exec(
                link_cmd(remote_src, self._r_testplan_ppath),
                label=f"link remote-exisiting testplan path {remote_src} to "
                f"{self.cfg._runpath_testplan_dir} under runpath",
            )
        return remote_src

    def remote_teardown_pyenv(self):
        # everything under runpath, should be auto removed
        pass

    def get_remote_rpyc_bin(self) -> str:
        import rpyc

        return os.path.join(
            os.path.dirname(rpyc.__file__),
            os.pardir,
            os.pardir,
            "bin",
            "rpyc_classic.py",
        )


# TODO
# class OCIContainerBasedBuilder(RuntimeBuilder): ...
