import os.path
import shlex
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable
from typing_extensions import TypeAlias  # available in Python 3.10+

from testplan.common.utils.path import module_abspath
from testplan.common.utils.remote import filepath_exist_cmd, link_cmd

CmdExecF: TypeAlias = Callable[..., tuple[int, str, str]]


class RuntimeSetupMethod(Enum):
    PIP_BASED = "pip"
    SIMPLE_SYSPATH = "syspath"
    # OCI_CONTAINER = "container"

    @property
    def implementation(self) -> type["RuntimeSetup"]:
        if self == RuntimeSetupMethod.PIP_BASED:
            return PipBasedSetup
        # elif self == RuntimeSetupMethod.SIMPLE_SYSPATH:
        else:
            return SimpleSyspathSetup
        # elif self == RuntimeSetupMethod.OCI_CONTAINER:
        # else:
        #     return OCIContainerBasedSetup


class RuntimeSetup(ABC):
    def __init__(
        self,
        remote_runpath: str,
        local_cmd_exec: CmdExecF,
        remote_cmd_exec: CmdExecF,
        parent_cfg,
    ):
        self._remote_runpath = remote_runpath
        self._lcmd_exec = local_cmd_exec
        self._rcmd_exec = remote_cmd_exec
        self._cfg = parent_cfg

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


class PipBasedSetup(RuntimeSetup):
    VENV_UNDER_RUNPATH = "venv"

    def __init__(
        self, remote_runpath, local_cmd_exec, remote_cmd_exec, parent_cfg
    ):
        super().__init__(
            remote_runpath, local_cmd_exec, remote_cmd_exec, parent_cfg
        )
        self._upstream_pkgs = None
        self._remote_python_bin = None

    @staticmethod
    def group_freezed(packages: list):
        # NOTE: only uv will return local dirs instead of vcs path
        # TODO: uv behaviour to be verified
        upstream = []
        local = []
        for p in packages:
            if p.startswith("-e "):
                local.append(p[3:])
            elif " @ " in p:
                p_ = p.split(" @ ")[1]
                if p_.startswith("file://"):
                    local.append(p_)
                else:
                    # assuming package index reachable from remote
                    upstream.append(p_)
            else:
                upstream.append(p)

        return upstream, local

    def remote_python_detect(self):
        local_use_sys_env = sys.base_prefix == sys.prefix
        remote_base_bin = self._cfg.remote_python_bin

        if self._cfg.remote_use_sys_env:
            return remote_base_bin
        if not local_use_sys_env:
            # test if local venv accessible on remote
            # NOTE: this is obviously a quite rough test
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
        venv_path = os.path.join(self._remote_runpath, self.VENV_UNDER_RUNPATH)
        # FIXME: tmp workaround for &&, since shlex.quote only applied on list
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
        # TODO: if IS_WIN
        self._remote_python_bin = os.path.join(venv_path, "bin", "python3")
        return self._remote_python_bin

    def local_env_export(self):
        import uv  # so that usage of uv noticed by linter

        _, stdout, _ = self._lcmd_exec(
            [sys.executable, "-m", uv.__name__, "pip", "freeze"],
            label="execute uv pip freeze locally",
        )
        upstream, local = PipBasedSetup.group_freezed(stdout.splitlines())
        self._upstream_pkgs = upstream
        # TODO: remove assertion
        assert all(
            map(lambda x: "file://" == x[:7] and x[-1] != os.sep, local)
        ), f"FIXME: unexpected value in {local}"
        local_paths = [x[7:] for x in local]
        return list(
            map(
                lambda x: (
                    x,
                    os.path.join(
                        self._remote_runpath,
                        "local_package",
                        x.rsplit(os.sep, 1)[1],
                    ),
                ),
                local_paths,
            )
        )

    def remote_env_setup(self, remote_paths):
        import uv  # so that usage of uv noticed by linter

        assert self._upstream_pkgs  # FIXME: remove assertion
        self._rcmd_exec(
            [self._remote_python_bin, "-m", "pip", "install", uv.__name__],
            label="install uv on remote",
        )
        self._rcmd_exec(
            [
                self._remote_python_bin,
                "-m",
                uv.__name__,
                "pip",
                "install",
                *self._upstream_pkgs,
                *remote_paths,
            ],
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
        # TODO: should return None once child.py is invoked with -m instead full path
        return r_testplan_parent

    def remote_env_teardown(self):
        # everything under runpath, should be auto removed
        pass


class SimpleSyspathSetup(RuntimeSetup):
    DIR_UNDER_RUNPATH = "testplan_lib"

    def __init__(
        self, remote_runpath, local_cmd_exec, remote_cmd_exec, parent_cfg
    ):
        super().__init__(
            remote_runpath, local_cmd_exec, remote_cmd_exec, parent_cfg
        )
        import testplan

        self._l_testplan_path = os.path.dirname(
            os.path.dirname(module_abspath(testplan))
        )
        self._r_testplan_path = os.path.join(
            self._remote_runpath, self.DIR_UNDER_RUNPATH
        )

    def remote_python_detect(self) -> str:
        return self._cfg.remote_python_bin

    def local_env_export(self) -> list:
        if (
            self._cfg.testplan_path
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
        if self._cfg.testplan_path:
            remote_src = self._cfg.testplan_path
            self._rcmd_exec(
                link_cmd(remote_src, self._r_testplan_path),
                label=f"link user-specified testplan path {remote_src} to testplan_lib under runpath",
            )
        elif remote_paths:
            remote_src = remote_paths[0]
            # TODO: remove assertion
            assert remote_src == self._r_testplan_path
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
# class OCIContainerBasedSetup(RuntimeSetup): ...
