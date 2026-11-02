import os
import shlex
from unittest.mock import Mock

import pytest

from testplan.common.remote.remote_runtime import PipBasedBuilder

uv = pytest.importorskip("uv")

R_RUNPATH = "/remote/runpath"
R_PYTHON = "/remote/venv/bin/python3"


def _make_builder(overridden_deps, **options):
    builder = PipBasedBuilder(overridden_deps=overridden_deps, **options)
    builder._r_runpath = R_RUNPATH
    builder._remote_python_bin = R_PYTHON
    builder._lcmd_exec = Mock()
    builder._rcmd_exec = Mock(return_value=(0, "/remote/site-packages", ""))
    return builder


def _install_cmd(builder):
    for call in builder._rcmd_exec.call_args_list:
        if call.kwargs.get("label") == "install packages on remote":
            return call.args[0]
    raise AssertionError("install packages command not executed")


@pytest.mark.parametrize(
    "deps, expected_local",
    [
        (["pkgA==1.0", "pkgB"], []),
        (
            [
                "pkgA==1.0",
                "pkgB @ file:///local/dist/pkgB-1.0-py3-none-any.whl",
                "-e file:///local/src/pkgC",
            ],
            [
                os.path.join(
                    R_RUNPATH,
                    "local_packages",
                    "pkgB-1.0-py3-none-any.whl",
                ),
                os.path.join(R_RUNPATH, "local_packages", "pkgC"),
            ],
        ),
    ],
    ids=["no_local_packages", "with_local_packages"],
)
def test_pip_builder_install_cmd(deps, expected_local):
    builder = _make_builder(deps)

    transfers = builder.local_export_pyenv()
    builder._lcmd_exec.assert_not_called()
    # each local package is copied into the local_packages dir, so it must
    # land exactly at the path later passed to "uv pip install"
    local_pkg_dir = os.path.join(R_RUNPATH, "local_packages", "")
    assert all(dst == local_pkg_dir for _, dst in transfers)
    assert [
        os.path.join(local_pkg_dir, os.path.basename(src))
        for src, _ in transfers
    ] == expected_local

    assert builder.remote_setup_pyenv([]) == "/remote/site-packages"

    cmd = _install_cmd(builder)
    # an argument list, so no shell glob is left for the remote side to
    # expand (or fail to expand when there are no local packages)
    assert isinstance(cmd, list)
    assert not any("*" in arg for arg in cmd)
    assert cmd == [
        R_PYTHON,
        "-m",
        uv.__name__,
        "pip",
        "install",
        *[d for d in deps if "file://" not in d],
        *expected_local,
    ]


def test_pip_builder_extra_install_args():
    extra = ["--only-binary=:all:", "--no-binary=qpython"]
    builder = _make_builder(["pkgA==1.0"], extra_install_args=extra)

    builder.local_export_pyenv()
    builder.remote_setup_pyenv([])

    cmd = _install_cmd(builder)
    assert cmd == [
        R_PYTHON,
        "-m",
        uv.__name__,
        "pip",
        "install",
        *extra,
        "pkgA==1.0",
    ]


def test_pip_builder_extra_install_args_not_shell_interpreted():
    builder = _make_builder(
        ["pkgA==1.0"], extra_install_args=["evil; rm -rf /tmp/x"]
    )

    builder.local_export_pyenv()
    builder.remote_setup_pyenv([])

    cmd = _install_cmd(builder)
    assert "evil; rm -rf /tmp/x" in cmd
    assert "'evil; rm -rf /tmp/x'" in shlex.join(cmd)
