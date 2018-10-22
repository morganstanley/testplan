"""TODO."""

import os
import psutil

from testplan import Testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.report.testing import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.path import fix_home_prefix
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import MultiTestConfig


@testsuite
class MySuite(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(env.cfg.name)


def get_mtest(name):
    """TODO."""
    return MultiTest(name='MTest{}'.format(name), suites=[MySuite()])


def get_mtest_imported(name):
    """TODO."""
    return MultiTest(name='MTest{}'.format(name), suites=[MySuite()])


@testsuite
class SuiteKillingWorker(object):

    def __init__(self, parent_pid, size):
        self._parent_pid = parent_pid
        self._size = size

    @testcase
    def test_comparison(self, env, result):
        parent = psutil.Process(self._parent_pid)
        if len(parent.children(recursive=True)) == self._size:
            print('Killing worker {}'.format(os.getpid()))
            os.kill(os.getpid(), 9)
        result.equal(1, 1, 'equality description')
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(env.cfg.name)


def multitest_kill_one_worker(name, parent_pid, size):
    """Test that kills one worker."""
    return MultiTest(name='MTest{}'.format(name),
                     suites=[SuiteKillingWorker(parent_pid, size)])


def multitest_kills_worker():
    """To kill all child workers."""
    os.kill(os.getpid(), 9)


def schedule_tests_to_pool(name, pool, **pool_cfg):
    pool_name = pool.__name__

    # Enable debug:
    from testplan.logger import DEBUG
    TESTPLAN_LOGGER.setLevel(DEBUG)

    plan = Testplan(
        name=name,
        parse_cmdline=False
    )
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)

    this_file = fix_home_prefix(os.path.dirname(os.path.abspath(__file__)))
    if pool_cfg.get('workspace'):  # Remote pool
        ws = pool_cfg['workspace']
        wd = fix_home_prefix(os.getcwd())
        common = os.path.commonprefix(
            [pool_cfg['workspace'], wd])

        # Relative path tp the same file but from the remote workspace.
        path = '/'.join(os.path.join(
            os.path.relpath(common, wd),
            os.path.relpath(this_file, ws)
        ).split(os.sep))
    else:
        path = this_file

    uids = []
    for idx in range(1, 10):
        uids.append(plan.schedule(target='get_mtest',
                                  module='func_pool_base_tasks',
                                  path=path, kwargs=dict(name=idx),
                                  resource=pool_name))

    res = plan.run()

    assert res.run is True
    assert res.success is True
    assert plan.report.passed is True
    assert plan.report.status == Status.PASSED
    assert plan.report.counts.passed == 9
    assert plan.report.counts.error == plan.report.counts.skipped == \
           plan.report.counts.failed == plan.report.counts.incomplete == 0

    names = sorted(['MTest{}'.format(x) for x in range(1, 10)])
    assert sorted([entry.name for entry in plan.report.entries]) == names

    assert isinstance(plan.report.serialize(), dict)

    for idx in range(1, 10):
        name = 'MTest{}'.format(idx)
        assert plan.result.test_results[uids[idx-1]].report.name == name

    # All tasks scheduled once
    for uid in pool.task_assign_cnt:
        assert pool.task_assign_cnt[uid] == 1
