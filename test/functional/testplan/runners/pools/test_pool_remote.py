"""Remote worker pool unit tests."""

import os
import pytest
import platform

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


@pytest.mark.skipif(
    IS_WIN,
    reason='Remote pool is skipped on Windows.'
)
def test_pool_basic():
    """Basic test scheduling."""
    import testplan
    workspace = os.path.abspath(
        os.path.join(
            os.path.dirname(module_abspath(testplan)),
            '..', '..'))

    for remote_pool_type in ('thread', 'process'):
        schedule_tests_to_pool(
            'RemotePlan', RemotePool,
            hosts={'localhost': 2},
            ssh_cmd=mock_ssh,
            copy_cmd=strip_host,
            workspace=workspace,
            copy_workspace_check=None,
            pool_type=remote_pool_type)
