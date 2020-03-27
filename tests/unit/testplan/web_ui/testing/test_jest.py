"""Run tests for the UI code."""
import subprocess
import os

import pytest

from testplan import web_ui

TESTPLAN_UI_DIR = os.path.abspath(
    os.path.join(os.path.dirname(web_ui.__file__), "testing")
)


def npm_installed():
    """Check if npm has been installed."""
    with open(os.devnull, "w") as FNULL:
        try:
            subprocess.check_call("npm --version", shell=True, stdout=FNULL)
        except subprocess.CalledProcessError:
            return False
        else:
            return True


def tp_ui_installed():
    """Check if the Testplan UI dependencies have been installed."""
    node_modules_dir = os.path.join(TESTPLAN_UI_DIR, "node_modules")
    print(os.path.abspath(node_modules_dir))
    return os.path.exists(node_modules_dir)


@pytest.mark.skipif(
    not (npm_installed() and tp_ui_installed()),
    reason="requires npm & testplan UI to have been installed.",
)
def test_testplan_ui():
    """Run the Jest unit tests for the UI."""
    env = os.environ.copy()
    env["CI"] = "true"
    subprocess.check_call("npm test", shell=True, cwd=TESTPLAN_UI_DIR, env=env)


@pytest.mark.skipif(
    not (npm_installed() and tp_ui_installed()),
    reason="requires npm & testplan UI to have been installed.",
)
def test_eslint():
    """Run eslint over the UI source code."""
    subprocess.check_call("npm run lint", shell=True, cwd=TESTPLAN_UI_DIR)
