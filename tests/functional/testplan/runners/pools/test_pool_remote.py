"""Remote worker pool functional tests."""

import os
import pytest
import platform
import shutil
import tempfile
import subprocess

import testplan
from testplan.runners.pools import RemotePool
from testplan.common.utils.remote import copy_cmd
from .func_pool_base_tasks import schedule_tests_to_pool

IS_WIN = platform.system() == "Windows"


def mock_ssh(host, command):
    """Avoid network connection."""
    return ["/bin/sh", "-c", command]


def strip_host(source, target, **kwargs):
    """Avoid network connection."""
    if ":" in source:
        source = source.split(":")[1]
    if ":" in target:
        target = target.split(":")[1]
    return copy_cmd(source, target)


def copytree(src, dst):
    """
    We can't use shutil.copytree() with python 3.4.4 due to
    https://bugs.python.org/issue21697 so use rsync instead.
    """
    subprocess.check_call(
        [
            "rsync",
            "-rL",
            "--exclude=.git",
            "--exclude=*.pyc",
            "--exclude=*__pycache__*",
            src,
            dst,
        ]
    )


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

    tmp_tests_dir = os.path.join(workspace, "tests")

    copytree("{}{}".format(orig_tests_dir, os.path.sep), tmp_tests_dir)

    # We need to schedule tests from the directory of this script but within
    # the workspace.
    schedule_path = os.path.join(
        "tests", os.path.relpath(script_dir, orig_tests_dir)
    )

    return workspace, schedule_path


@pytest.mark.skipif(IS_WIN, reason="Remote pool is skipped on Windows.")
def test_pool_basic():
    """Basic test scheduling."""
    workspace, schedule_path = setup_workspace()

    try:
        # Make sure our current working directory is within the workspace -
        # testplan requires this.
        orig_dir = os.getcwd()
        os.chdir(workspace)

        for remote_pool_type in ("thread", "process"):
            schedule_tests_to_pool(
                "RemotePlan",
                RemotePool,
                hosts={"localhost": 2},
                ssh_cmd=mock_ssh,
                copy_cmd=strip_host,
                workspace=workspace,
                copy_workspace_check=None,
                pool_type=remote_pool_type,
                schedule_path=schedule_path,
            )
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(workspace)
