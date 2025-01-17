"""Remote worker pool functional tests."""

import os
import shutil
import tempfile

import pytest

from testplan.common.utils.process import execute_cmd
from testplan.common.utils.remote import ssh_cmd
from testplan.report import Status
from testplan.runners.pools.remote import RemotePool
from tests.functional.testplan.runners.pools.test_pool_base import (
    schedule_tests_to_pool,
    schedule_tests_to_remote_pool_on_specific_worker
)

REMOTE_HOST = os.environ.get("TESTPLAN_REMOTE_HOST")
TESTPLAN_REMOTE_HOST1 = os.environ.get("TESTPLAN_REMOTE_HOST1")
TESTPLAN_REMOTE_HOST2 = os.environ.get("TESTPLAN_REMOTE_HOST2")

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
        assert 0 == execute_cmd(
            ssh_cmd({"host": REMOTE_HOST}, f"test -L {workspace}"),
            label="workspace imitated on remote",
            check=False,
        )
        os.chdir(orig_dir)
        shutil.rmtree(workspace)


@skip_on_windows(reason="Remote pool is skipped on Windows.")
@pytest.mark.parametrize("remote_pool_type", ("thread", "process"))
def test_run_task_with_specific_worker_on_remote_pool(mockplan, remote_pool_type):
    """Schedule task for specific worker on remote pool."""
    workspace, schedule_path = setup_workspace()

    try:
        # Make sure our current working directory is within the workspace -
        # testplan requires this.
        orig_dir = os.getcwd()
        os.chdir(workspace)

        schedule_tests_to_remote_pool_on_specific_worker(
            mockplan,
            RemotePool,
            hosts={
                TESTPLAN_REMOTE_HOST1: 2,
                TESTPLAN_REMOTE_HOST2: 2,
            },
            workspace=workspace,
            pool_type=remote_pool_type,
            schedule_path=schedule_path,
            restart_count=0,
            clean_remote=True,
        )
    finally:
        assert 0 == execute_cmd(
            ssh_cmd({"host": REMOTE_HOST}, f"test -L {workspace}"),
            label="workspace imitated on remote",
            check=False,
        )
        os.chdir(orig_dir)
        shutil.rmtree(workspace)


def test_materialization_fail(mockplan):
    """Test task target will fail to materialize in worker"""
    pool_name = RemotePool.__name__
    pool = RemotePool(
        name=pool_name,
        hosts={REMOTE_HOST: 1},
        workspace_exclude=["*"],  # effectively not copy anything
        clean_remote=True,
    )
    mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))
    mockplan.schedule(
        target="target_raises_in_worker",
        module="func_pool_base_tasks",
        path=dirname,
        args=(os.getpid(),),
        resource=pool_name,
    )

    res = mockplan.run()

    assert res.run is False
    assert res.success is False
    assert mockplan.report.status == Status.ERROR
    assert (
        mockplan.report.entries[0].name
        == "Task[target_raises_in_worker(uid=MTest)]"
    )
    assert (
        mockplan.report.entries[0].category
        == Status.ERROR.to_json_compatible()
    )
