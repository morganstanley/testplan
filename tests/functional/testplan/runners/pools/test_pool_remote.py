"""Remote worker pool unit tests."""

import os
import pytest
import platform
import shutil
import tempfile
import subprocess

import testplan
from testplan.runners.pools import RemotePool
from testplan.common.utils.path import module_abspath
from testplan.common.utils.remote import copy_cmd
from .func_pool_base_tasks import schedule_tests_to_pool

IS_WIN = platform.system() == 'Windows'


def mock_ssh(host, command):
    """Avoid network connection."""
    return ['/bin/sh', '-c', command]


def strip_host(source, target, **kwargs):
    """Avoid network connection."""
    if ':' in source:
        source = source.split(':')[1]
    if ':' in target:
        target = target.split(':')[1]
    return copy_cmd(source, target)


def copytree(src, dst):
    """
    We can't use shutil.copytree() with python 3.4.4 due to
    https://bugs.python.org/issue21697 so use rsync instead.
    """
    subprocess.check_call(
        ['rsync', '-rL', '--exclude=.git', '--exclude=*.pyc', '--exclude=__pycache__', src, dst])


def setup_workspace():
    """
    Sets up the workspace to use for testing the remote pool. We need two
    directories in the workspace: "testplan" containing the testplan package,
    and "test" containing tests to be scheduled.

    :return: paths to the workspace root and where to schedule tests from.
    """
    # Set up the workspace in a temporary directory.
    workspace = tempfile.mkdtemp()

    # First copy the testplan package into the "testplan" dir within the
    # workspace.
    orig_pkg_dir = os.path.dirname(testplan.__file__)
    copytree(orig_pkg_dir, workspace)

    # Next copy the test dir. "test" is a generic name so we don't want to rely
    # on "import test" here - instead rely on the test directory being 4 levels
    # above the directory this script is in.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    orig_test_dir = os.path.abspath(
        os.path.join(script_dir, *(os.pardir for _ in range(4))))
    tmp_test_dir = os.path.join(workspace, 'test')
    copytree('{}{}'.format(orig_test_dir, os.path.sep), tmp_test_dir)

    # We need to schedule tests from the directory of this script but within
    # the workspace.
    schedule_path = os.path.join(tmp_test_dir,
                                 os.path.relpath(script_dir, orig_test_dir))

    return workspace, schedule_path

@pytest.mark.skipif(
    IS_WIN,
    reason='Remote pool is skipped on Windows.'
)
def test_pool_basic():
    """Basic test scheduling."""
    workspace, schedule_path = setup_workspace()

    try:
        # Make sure our current working directory is within the workspace -
        # testplan requires this.
        orig_dir = os.getcwd()
        os.chdir(workspace)

        for remote_pool_type in ('thread', 'process'):
            schedule_tests_to_pool(
                'RemotePlan', RemotePool,
                hosts={'localhost': 2},
                ssh_cmd=mock_ssh,
                copy_cmd=strip_host,
                workspace=workspace,
                copy_workspace_check=None,
                pool_type=remote_pool_type,
                schedule_path=schedule_path)
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(workspace)
