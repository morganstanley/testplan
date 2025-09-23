# XXX: pathlib?

import os.path
import shlex
import sys
from abc import ABC, abstractmethod
from typing import Callable

import uv  # so that usage of uv noticed by linter
from typing_extensions import TypeAlias  # available in Python 3.10+

from testplan.common.config import Config, ConfigOption
from testplan.common.entity import Entity
from testplan.common.utils.path import module_abspath
from testplan.common.utils.remote import filepath_exist_cmd, link_cmd, rm_cmd

CmdExecF: TypeAlias = Callable[..., tuple[int, str, str]]


class RuntimeBuilder(Entity, ABC):
    def __init__(self, **options):
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
        self._l_runpath = local_runpath
        self._r_runpath = remote_runpath
        self._lcmd_exec = local_cmd_exec
        self._rcmd_exec = remote_cmd_exec
        self.cfg.parent = parent_cfg

    @abstractmethod
    def remote_python_detect(self) -> str: ...

    @abstractmethod
    def local_env_export(self) -> list[tuple[str, str]]: ...

    @abstractmethod
    def remote_env_setup(
        self,
        remote_paths: list[str],
    ) -> str: ...  # FIXME: change to optional once child.py invokable through module name

    @abstractmethod
    def remote_env_teardown(self): ...


class RuntimeBuilderConfig(Config):
    # TODO: python ver check flag & local ver info?
    @classmethod
    def get_options(cls):
        return {}


class PipBasedBuilderConfig(RuntimeBuilderConfig):
    @classmethod
    def get_options(cls):
        return {
            ConfigOption("remote_python_base_bin", default="python3"): str,
            ConfigOption("remote_use_sys_env", default=False): bool,
            ConfigOption(
                "remote_venv_dest", default=None
            ): str,  # validation postponed to py detect
            ConfigOption("remote_reuse_venv_if_exists", default=False): bool,
            ConfigOption("_remote_runpath_venv_name", default="venv"): str,
            ConfigOption(
                "_remote_runpath_package_dir", default="local_packages"
            ): str,
        }


class PipBasedBuilder(RuntimeBuilder):
    CONFIG = PipBasedBuilderConfig

    def __init__(self, **options):
        super().__init__(**options)
        self._upstream_pkgs: list[str]
        self._local_pkgs: list[str]  # local from the perspective of remote
        self._remote_python_bin: str

    @staticmethod
    def group_freezed(packages: list):
        # NOTE: impl relies on behaviour of "uv pip freeze"
        upstream = []
        local = []
        for p in packages:
            # "uv pip freeze"-exported editable must be local dirs
            # (``pip install -e`` will create ``src`` under ``sys.prefix``)
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

    def remote_python_detect(self):
        remote_base_bin = self.cfg.remote_python_bin  # from parent cfg

        if self.cfg.remote_use_sys_env:
            return remote_base_bin

        local_use_sys_env = sys.base_prefix == sys.prefix
        if not local_use_sys_env:
            # test if local venv accessible on remote, e.g. via nfs, reuse it
            # XXX: shall we allow this behaviour? we don't have proper arch test
            if (
                self._rcmd_exec(
                    filepath_exist_cmd(sys.prefix),
                    label="test if local venv accessible on remote",
                    check=False,
                )[0]
                == 0
            ):
                self._remote_python_bin = sys.executable
                return self._remote_python_bin

        if self.cfg.remote_venv_dest:
            if (
                self._rcmd_exec(
                    filepath_exist_cmd(self.cfg.remote_venv_dest),
                    label="test if remote_venv_dest exists",
                    check=False,
                )[0]
                == 0
            ):
                if self.cfg.remote_reuse_venv_if_exists:
                    self._remote_python_bin = self.deduce_python_bin(
                        self.cfg.remote_venv_dest
                    )
                    return self._remote_python_bin
                self._rcmd_exec(
                    rm_cmd(self.cfg.remote_venv_dest),
                    label="remove existing remote_venv_dest",
                )
            venv_path = self.cfg.remote_venv_dest
        else:
            venv_path = os.path.join(
                self._r_runpath, self.cfg._remote_runpath_venv_name
            )
        # XXX: tmp workaround, since shlex.quote only applied on list
        self._rcmd_exec(
            " ".join(
                [
                    "mkdir",
                    "-p",
                    shlex.quote(venv_path),
                    "&&",
                    shlex.quote(remote_base_bin),
                    "-m",
                    "venv",
                    shlex.quote(venv_path),
                ]
            ),
            label="create remote venv",
        )
        self._remote_python_bin = self.deduce_python_bin(venv_path)
        return self._remote_python_bin

    def local_env_export(self):
        _, stdout, _ = self._lcmd_exec(
            [sys.executable, "-m", uv.__name__, "pip", "freeze"],
            label="execute uv pip freeze locally",
        )
        self._upstream_pkgs, local = self.group_freezed(stdout.splitlines())

        self.logger.info("local packages to transfer: %s", local)
        self._local_pkgs = [
            os.path.join(
                self._r_runpath,
                self.cfg._remote_runpath_package_dir,
                x.rsplit(os.sep, 1)[1],
            )
            for x in local
        ]
        return list(
            map(
                lambda x: (
                    x,
                    os.path.join(
                        self._r_runpath,
                        self.cfg._remote_runpath_package_dir,
                        "*",  # force creation of parent package dir
                    ),
                ),
                local,
            )
        )

    def remote_env_setup(self, remote_paths):
        self._rcmd_exec(
            [self._remote_python_bin, "-m", "pip", "install", uv.__name__],
            label="install uv on remote",
        )
        # XXX: tmp workaround, since shlex.quote only applied on list
        # XXX: self._upstream_pkgs to requirements.txt?
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
            + f" {shlex.quote(os.path.join(self._r_runpath, self.cfg._remote_runpath_package_dir))}/*",
            label="install packages on remote",
        )
        _, r_testplan_parent, _ = self._rcmd_exec(
            [
                self._remote_python_bin,
                "-c",
                "import testplan, os.path; "
                "print(os.path.dirname(os.path.dirname(testplan.__file__)), end='')",
            ],
            label="get remote testplan parent dir",
        )
        # XXX: should return None once child.py is invoked with -m instead full path
        return r_testplan_parent

    def remote_env_teardown(self):
        # everything under runpath, should be auto removed
        pass


class SimpleSyspathBuilderConfig(RuntimeBuilderConfig):
    @classmethod
    def get_options(cls):
        return {
            ConfigOption("runpath_testplan_dir", default="testplan_lib"): str,
        }


class SimpleSyspathBuilder(RuntimeBuilder):
    CONFIG = SimpleSyspathBuilderConfig

    def __init__(self, **options):
        super().__init__(**options)
        self._l_testplan_path: str
        self._r_testplan_path: str

    def bootstrap(self, *args, **kwargs):
        super().bootstrap(*args, **kwargs)
        import testplan

        self._l_testplan_path = os.path.dirname(
            os.path.dirname(module_abspath(testplan))
        )
        self._r_testplan_path = os.path.join(
            self._r_runpath, self.cfg.runpath_testplan_dir
        )

    def remote_python_detect(self) -> str:
        return self.cfg.remote_python_bin

    def local_env_export(self) -> list:
        if (
            self.cfg.testplan_path
        ):  # remote path specified, no need to transfer files
            return []

        # NOTE: this is obviously a quite rough test
        if (
            self._rcmd_exec(
                filepath_exist_cmd(self._l_testplan_path),
                label="test if testplan accessible on remote",
                check=False,
            )[0]
            == 0
        ):
            return []
        return [
            (
                self._l_testplan_path,
                self._r_testplan_path,
            )
        ]

    def remote_env_setup(self, remote_paths):
        if self.cfg.testplan_path:
            remote_src = self.cfg.testplan_path
            self._rcmd_exec(
                link_cmd(remote_src, self._r_testplan_path),
                label=f"link user-specified testplan path {remote_src} to testplan_lib under runpath",
            )
        elif remote_paths:
            remote_src = self._r_testplan_path
            # no need to make symlink
        else:
            remote_src = self._l_testplan_path
            self._rcmd_exec(
                link_cmd(remote_src, self._r_testplan_path),
                label=f"link remote-exisiting testplan path {remote_src} to testplan_lib under runpath",
            )
        return remote_src

    def remote_env_teardown(self):
        # everything under runpath, should be auto removed
        pass


# TODO
# class OCIContainerBasedBuilder(RuntimeBuilder): ...
