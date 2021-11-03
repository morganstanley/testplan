"""Remote worker pool functional tests."""

import os
import pytest
import shutil
import tempfile

from testplan.runners.pools.remote import RemotePool

from .func_pool_base_tasks import schedule_tests_to_pool

REMOTE_HOST = os.environ.get("TESTPLAN_REMOTE_HOST")
pytestmark = pytest.mark.skipif(
    not REMOTE_HOST,
    reason="Remote host not specified, skip remote pool test",
)
# tests/helpers are on the pythonpath
from pytest_test_filters import skip_on_windows


def setup_workspace():
    """
    Sets up the workspace to use for testing the remote pool. We will copy the
    tests subdir to workspace, and remote pool logic will copy the workspace
    to remote host.

    :return: paths to the workspace root and where to schedule tests from.
    """
    # Set up the workspace in a temporary directory.
    workspace = tempfile.mkdtemp()

    # Copy the tests dir. "tests" is a generic name so we don't want to
    # rely "import tests" here - instead navigate up to find the tests dir.
    script_dir = os.path.dirname(__file__)

    orig_tests_dir = script_dir
    while os.path.basename(orig_tests_dir) != "tests":
        orig_tests_dir = os.path.abspath(
            os.path.join(orig_tests_dir, os.pardir)
        )

    shutil.copytree(orig_tests_dir, os.path.join(workspace, "tests"))

    # We need to schedule tests from the directory of this script but within
    # the workspace.
    schedule_path = os.path.join(
        "tests", os.path.relpath(script_dir, orig_tests_dir)
    )

    return workspace, schedule_path


@skip_on_windows(reason="Remote pool is skipped on Windows.")
@pytest.mark.parametrize("remote_pool_type", ("thread", "process"))
def test_pool_basic(mockplan, remote_pool_type):
    """Basic test scheduling."""
    workspace, schedule_path = setup_workspace()

    try:
        # Make sure our current working directory is within the workspace -
        # testplan requires this.
        orig_dir = os.getcwd()
        os.chdir(workspace)

        schedule_tests_to_pool(
            mockplan,
            RemotePool,
            hosts={REMOTE_HOST: 2},
            workspace=workspace,
            pool_type=remote_pool_type,
            schedule_path=schedule_path,
            restart_count=0,
            clean_remote=True,
        )
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(workspace)
