"""Process worker pool functional tests."""

import os

import pytest

from testplan.common.utils.testing import log_propagation_disabled
from testplan.report.testing import Status
from testplan.runners.pools import ProcessPool
from testplan import Testplan
from testplan.common.utils.logger import TESTPLAN_LOGGER

from .func_pool_base_tasks import schedule_tests_to_pool


def test_pool_basic():
    """Basic test scheduling."""
    schedule_tests_to_pool('ProcPlan', ProcessPool,
                           worker_heartbeat=2,
                           heartbeats_miss_limit=2)


def test_kill_one_worker():
    """Kill one worker but pass after reassigning task."""
    pool_name = ProcessPool.__name__
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False,
    )
    pool_size = 4
    pool = ProcessPool(name=pool_name, size=pool_size,
                       worker_heartbeat=2,
                       heartbeats_miss_limit=2,
                       max_active_loop_sleep=1)
    pool_uid = plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    kill_uid = plan.schedule(target='multitest_kill_one_worker',
                             module='func_pool_base_tasks',
                             path=dirname,
                             args=('killer', os.getpid(),
                                   pool_size),  # kills 4th worker
                             resource=pool_name)

    uids = []
    for idx in range(1, 25):
        uids.append(plan.schedule(target='get_mtest',
                                  module='func_pool_base_tasks',
                                  path=dirname, kwargs=dict(name=idx),
                                  resource=pool_name))

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = plan.run()

    # Check that the worker killed by test was aborted
    assert len([worker for worker in plan.resources[pool_uid]._workers
                if worker._aborted is True]) == 1

    assert res.run is True
    assert res.success is True
    assert plan.report.status == Status.PASSED

    # All tasks scheduled once
    for uid in pool.task_assign_cnt:
        if uid == kill_uid:
            assert pool.task_assign_cnt[uid] == 2
        else:
            assert pool.task_assign_cnt[uid] == 1


def test_kill_all_workers():
    """Kill all workers and create a failed report."""
    pool_name = ProcessPool.__name__
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False,
    )
    pool_size = 4
    pool = ProcessPool(name=pool_name, size=pool_size,
                       task_retries_limit=pool_size,
                       worker_heartbeat=2,
                       heartbeats_miss_limit=2,
                       max_active_loop_sleep=1)
    pool_uid = plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    uid = plan.schedule(target='multitest_kills_worker',
                        module='func_pool_base_tasks',
                        path=dirname, resource=pool_name)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = plan.run()

    # Check that the worker killed by test was aborted
    assert len([worker for worker in plan.resources[pool_uid]._workers
                if worker._aborted is True]) == pool_size

    assert res.success is False
    # scheduled X times and killed all workers
    assert pool.task_assign_cnt[uid] == pool_size
    assert plan.report.status == Status.ERROR


def test_reassign_times_limit():
    """Kill workers and reassign task up to limit times."""
    pool_name = ProcessPool.__name__
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False,
    )

    pool_size = 4
    retries_limit = int(pool_size / 2)
    pool = ProcessPool(name=pool_name, size=pool_size,
                       task_retries_limit=retries_limit,
                       worker_heartbeat=2,
                       heartbeats_miss_limit=2,
                       max_active_loop_sleep=1)
    pool_uid = plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    uid = plan.schedule(target='multitest_kills_worker',
                        module='func_pool_base_tasks',
                        path=dirname, resource=pool_name)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = plan.run()

    # Check that the worker killed by test was aborted
    assert len([worker for worker in plan.resources[pool_uid]._workers
                if worker._aborted is True]) == retries_limit

    assert res.success is False
    assert pool.task_assign_cnt[uid] == retries_limit
    assert plan.report.status == Status.ERROR


def test_custom_reschedule_condition():
    """Force reschedule task X times to test logic."""
    pool_name = ProcessPool.__name__
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False,
    )
    uid = 'custom_task_uid'
    max_reschedules = 2

    def custom_reschedule(pool, task_result):
        if pool.task_assign_cnt[uid] == max_reschedules:
            return False
        return True

    pool_size = 4
    pool = ProcessPool(name=pool_name, size=pool_size,
                       worker_heartbeat=2,
                       heartbeats_miss_limit=2,
                       max_active_loop_sleep=1)
    pool.set_reschedule_check(custom_reschedule)
    pool_uid = plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    plan.schedule(target='get_mtest',
                  module='func_pool_base_tasks',
                  path=dirname, kwargs=dict(name='0'),
                  resource=pool_name, uid=uid)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = plan.run()

    # Check that the worker killed by test was aborted
    assert len([worker for worker in plan.resources[pool_uid]._workers
                if worker._aborted is True]) == 0

    assert res.success is True
    assert pool.task_assign_cnt[uid] == max_reschedules
    assert plan.report.status == Status.PASSED


def test_unserializable_result():
    """
    Test scheduling a Task that stores a result which cannot be directly
    serialized by pickle. Even though the type inherits from a trivially
    serializalbe type (int), Testplan should still format it as a string
    before pickling.
    """
    # Set up a testplan and add a ProcessPool.
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False)

    pool = ProcessPool(name='ProcPool',
                       size=2)
    plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))
    plan.schedule(target='make_serialization_mtest',
                  module='func_pool_base_tasks',
                  path=dirname)

    # Run the plan and make standard assertions that the plan has passed.
    res = plan.run()
    assert res.run
    assert res.success
    assert plan.report.passed
    assert plan.report.status == Status.PASSED
    assert plan.report.counts.passed == 1
    assert plan.report.counts.error == 0
    assert plan.report.counts.skipped == 0
    assert plan.report.counts.failed == 0
    assert plan.report.counts.incomplete == 0

    # Dig down into the assertion result and check that the expected string
    # format for our UnPickleableInt is stored.
    assert len(plan.report.entries) == 1
    mtest_report = plan.report.entries[0]
    assert mtest_report.category == 'multitest'
    assert len(mtest_report.entries) == 1

    suite_report = mtest_report.entries[0]
    assert suite_report.category == 'suite'
    assert len(suite_report.entries) == 1

    testcase_report = suite_report.entries[0]
    assert len(testcase_report.entries) == 1

    assertion_result = testcase_report.entries[0]
    assert assertion_result['first'] == 'UnPickleableInt[42]'
    assert assertion_result['second'] == 42


def test_schedule_from_main():
    """
    Test scheduling Tasks from __main__ - it should not be allowed for
    ProcessPool.
    """
    # Set up a testplan and add a ProcessPool.
    plan = Testplan(
        name='ProcPlan',
        parse_cmdline=False)

    pool = ProcessPool(name='ProcPool',
                       size=2)
    plan.add_resource(pool)

    # First check that scheduling a Task with module string of '__main__'
    # raises the expected ValueError.
    with pytest.raises(ValueError):
        plan.schedule(target='target',
                      module='__main__',
                      resource='ProcPool')


    # Secondly, check that scheduling a callable target with a __module__ attr
    # of __main__ also raises a ValueError.
    def callable_target():
        raise RuntimeError

    callable_target.__module__ = '__main__'

    with pytest.raises(ValueError):
        plan.schedule(target=callable_target, resource='ProcPool')
