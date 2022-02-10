"""
Runs tests for the UI code.
"""
import os
import subprocess

import pytest

from testplan import web_ui
from pytest_test_filters import skip_on_windows

TESTPLAN_UI_DIR = os.path.abspath(
    os.path.join(os.path.dirname(web_ui.__file__), "testing")
)


def is_manager_installed(command: str):
    """
    Checks if package manager is installed.
    """
    with open(os.devnull, "w") as FNULL:
        try:
            subprocess.check_call(
                f"{command} --version",
                shell=True,
                stdout=FNULL
            )
        except subprocess.CalledProcessError:
            return False
        else:
            return True


def tp_ui_installed():
    """
    Checks if the Testplan UI dependencies are installed.
    """
    node_modules_dir = os.path.join(TESTPLAN_UI_DIR, "node_modules")
    return os.path.exists(node_modules_dir)


@pytest.mark.skipif(
    not (is_manager_installed('pnpm') and tp_ui_installed()),
    reason="requires PNPM & testplan UI to be installed.",
)
def test_testplan_ui():
    """
    Runs the Jest unit tests for the UI.
    """
    env = os.environ.copy()
    env["CI"] = "true"
    subprocess.check_call(
        "pnpm test", shell=True, cwd=TESTPLAN_UI_DIR, env=env
    )


@skip_on_windows(reason="We run this on linux only")
@pytest.mark.skipif(
    not (is_manager_installed('pnpm') and tp_ui_installed()),
    reason="requires PNPM & testplan UI to be installed.",
)
def test_eslint():
    """
    Runs eslint over the UI source code.
    """
    subprocess.check_call("pnpm lint", shell=True, cwd=TESTPLAN_UI_DIR)
