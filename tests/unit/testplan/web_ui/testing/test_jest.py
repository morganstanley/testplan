"""Run tests for the UI code."""
import subprocess
import os

import pytest

from testplan import web_ui
from pytest_test_filters import skip_on_windows

TESTPLAN_UI_DIR = os.path.abspath(
    os.path.join(os.path.dirname(web_ui.__file__), "testing")
)


def is_npm_available() -> bool:
    """
    Checks if NPM is available.
    """
    with open(os.devnull, "w") as FNULL:
        try:
            subprocess.check_call("npm --version", shell=True, stdout=FNULL)
        except subprocess.CalledProcessError:
            return False
        else:
            return True


def tp_ui_installed() -> bool:
    """
    Checks if the Testplan UI dependencies are available.
    """
    node_modules_dir = os.path.join(TESTPLAN_UI_DIR, "node_modules")
    return os.path.exists(node_modules_dir)


@pytest.mark.skipif(
    not (is_npm_available() and tp_ui_installed()),
    reason="Requires NPM & Testplan UI to be available.",
)
def test_testplan_ui():
    """
    Run the Jest unit tests for the UI.
    """
    env = os.environ.copy()
    env["CI"] = "true"
    subprocess.check_call(
        "npm run test", shell=True, cwd=TESTPLAN_UI_DIR, env=env
    )


@skip_on_windows(reason="We run this on linux only")
@pytest.mark.skipif(
    not (is_npm_available() and tp_ui_installed()),
    reason="Requires NPM & Testplan UI to be available.",
)
def test_eslint():
    """
    Runs eslint over the UI source code.
    """
    subprocess.check_call("npm run lint", shell=True, cwd=TESTPLAN_UI_DIR)
