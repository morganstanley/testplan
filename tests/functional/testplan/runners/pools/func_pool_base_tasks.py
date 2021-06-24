"""Base Testplan Tasks shared by different functional tests."""

import os
import psutil

from testplan.report import Status
from testplan.common.utils.path import fix_home_prefix
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import MultiTestConfig
from testplan.common.utils.strings import slugify


@testsuite
class MySuite(object):
    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(slugify(env.cfg.name))


def get_mtest(name):
    """TODO."""
    return MultiTest(name="MTest{}".format(name), suites=[MySuite()])


def get_mtest_imported(name):
    """TODO."""
    return MultiTest(name="MTest{}".format(name), suites=[MySuite()])


@testsuite
class SuiteKillingWorker(object):
    def __init__(self, parent_pid, size):
        self._parent_pid = parent_pid
        self._size = size

    @testcase
    def test_comparison(self, env, result):
        parent = psutil.Process(self._parent_pid)
        if len(parent.children(recursive=False)) == self._size:
            print("Killing worker {}".format(os.getpid()))
            os.kill(os.getpid(), 9)
        result.equal(1, 1, "equality description")
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(slugify(env.cfg.name))


def multitest_kill_one_worker(parent_pid, size):
    """Test that kills one worker."""
    return MultiTest(
        name="MTestKiller", suites=[SuiteKillingWorker(parent_pid, size)]
    )


@testsuite
class SimpleSuite(object):
    @testcase
    def test_simple(self, env, result):
        pass


def multitest_kills_worker(parent_pid):
    """To kill all child workers."""
    if os.getpid() != parent_pid:  # Main process should not be killed
        os.kill(os.getpid(), 9)
    else:
        return MultiTest(name="MTestKiller", suites=[SimpleSuite()])


def schedule_tests_to_pool(plan, pool, schedule_path=None, **pool_cfg):
    pool_name = pool.__name__
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)

    if schedule_path is None:
        schedule_path = fix_home_prefix(
            os.path.dirname(os.path.abspath(__file__))
        )

    uids = []
    for idx in range(1, 10):
        uids.append(
            plan.schedule(
                target="get_mtest",
                module="func_pool_base_tasks",
                path=schedule_path,
                kwargs=dict(name=idx),
                resource=pool_name,
            )
        )

    res = plan.run()

    assert res.run is True
    assert res.success is True
    assert plan.report.passed is True
    assert plan.report.status == Status.PASSED
    # 1 testcase * 9 iterations
    assert plan.report.counter == {"passed": 9, "total": 9, "failed": 0}

    names = sorted(["MTest{}".format(x) for x in range(1, 10)])
    assert sorted([entry.name for entry in plan.report.entries]) == names

    assert isinstance(plan.report.serialize(), dict)

    for idx in range(1, 10):
        name = "MTest{}".format(idx)
        assert plan.result.test_results[uids[idx - 1]].report.name == name

    # All tasks assigned once
    for uid in pool._task_retries_cnt:
        assert pool._task_retries_cnt[uid] == 0
        assert pool.added_item(uid).reassign_cnt == 0
