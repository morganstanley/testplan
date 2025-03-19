"""Process worker pool functional tests."""

import os
from pathlib import Path

import pytest

from testplan.report import Status
from testplan.runners.pools.process import ProcessPool
from testplan.runners.pools.tasks import TaskMaterializationError
from testplan.runners.pools.tasks.base import task_target
from testplan.testing import multitest
from tests.functional.testplan.runners.pools.test_pool_base import (
    schedule_tests_to_pool,
)
from tests.unit.testplan.common.serialization import test_fields


def test_pool_basic(mockplan):
    """Basic test scheduling."""
    schedule_tests_to_pool(
        mockplan, ProcessPool, worker_heartbeat=2, heartbeats_miss_limit=2
    )


def test_kill_one_worker(mockplan, tmp_path: Path):
    """Kill one worker but pass after reassigning task."""
    pool_name = ProcessPool.__name__
    pool_size = 4
    pool = ProcessPool(
        name=pool_name,
        size=pool_size,
        worker_heartbeat=2,
        heartbeats_miss_limit=2,
        max_active_loop_sleep=1,
        restart_count=0,
    )
    pool_uid = mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    boobytrap = tmp_path / "boobytrap"
    boobytrap.touch()

    kill_uid = mockplan.schedule(
        target="multitest_kill_one_worker",
        module="func_pool_base_tasks",
        path=dirname,
        args=(str(boobytrap),),
        resource=pool_name,
    )

    uids = []
    for idx in range(1, 25):
        uids.append(
            mockplan.schedule(
                target="get_imported_mtest",
                module="func_pool_base_tasks",
                path=dirname,
                kwargs=dict(name=idx),
                resource=pool_name,
            )
        )

    res = mockplan.run()

    # Check that the worker killed by test was aborted
    assert (
        len(
            [
                worker
                for worker in mockplan.resources[pool_uid]._workers
                if worker._aborted is True
            ]
        )
        == 1
    )

    assert res.run is True
    assert res.success is True
    assert mockplan.report.status == Status.PASSED

    # local_runner, ProcessPool, and environments
    assert len(mockplan.report.children) == 3

    process_pool_entry = mockplan.report.children[2]
    assert process_pool_entry.name == "ProcessPool[ProcessPool]"
    assert "lifespan" in process_pool_entry.timer

    # ZMQServer + 4 workers
    assert len(process_pool_entry.children) == pool_size + 1
    assert process_pool_entry.children[1].name == "ProcessWorker[0]"
    assert "lifespan" in process_pool_entry.children[1].timer

    for entry in mockplan.report.entries:
        assert entry.host == "localhost"

    # All tasks scheduled once except the killed one
    for idx in range(1, 25):
        if uids[idx - 1] == kill_uid:
            assert pool._task_retries_cnt[uids[idx - 1]] == 1


def test_kill_all_workers(mockplan):
    """Kill all workers and create a failed report with incomplete status."""
    pool_name = ProcessPool.__name__
    pool_size = 4
    retries_limit = 3
    pool = ProcessPool(
        name=pool_name,
        size=pool_size,
        worker_heartbeat=2,
        heartbeats_miss_limit=2,
        max_active_loop_sleep=1,
        restart_count=0,
    )
    pool._task_retries_limit = retries_limit
    pool_uid = mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    uid = mockplan.schedule(
        target="multitest_kill_workers",
        module="func_pool_base_tasks",
        path=dirname,
        args=(os.getpid(),),
        resource=pool_name,
    )

    res = mockplan.run()

    # Check that the worker killed by test was aborted
    assert (
        len(
            [
                worker
                for worker in mockplan.resources[pool_uid]._workers
                if worker._aborted is True
            ]
        )
        == pool_size
    )

    assert res.success is False
    # scheduled X times and killed all workers
    assert pool._task_retries_cnt[uid] == retries_limit + 1
    assert mockplan.report.status == Status.INCOMPLETE


def test_reassign_times_limit(mockplan):
    """Kill workers and reassign task up to limit times."""
    pool_name = ProcessPool.__name__
    pool_size = 4
    retries_limit = int(pool_size / 2)
    pool = ProcessPool(
        name=pool_name,
        size=pool_size,
        worker_heartbeat=2,
        heartbeats_miss_limit=2,
        max_active_loop_sleep=1,
        restart_count=0,
    )
    pool._task_retries_limit = retries_limit
    pool_uid = mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    uid = mockplan.schedule(
        target="multitest_kill_workers",
        module="func_pool_base_tasks",
        path=dirname,
        args=(os.getpid(),),
        resource=pool_name,
    )

    res = mockplan.run()

    # Check that the worker killed by test was aborted
    assert (
        len(
            [
                worker
                for worker in mockplan.resources[pool_uid]._workers
                if worker._aborted is True
            ]
        )
        == retries_limit + 1
    )

    assert res.success is False
    assert pool._task_retries_cnt[uid] == retries_limit + 1
    assert mockplan.report.status == Status.ERROR
    assert mockplan.report.counter["error"] == 1


def test_disable_rerun_in_pool(mockplan):
    pool_name = ProcessPool.__name__
    uid = "custom_task_uid"
    rerun_limit = 2

    pool_size = 4
    pool = ProcessPool(
        name=pool_name,
        size=pool_size,
        worker_heartbeat=2,
        heartbeats_miss_limit=2,
        max_active_loop_sleep=1,
        restart_count=0,
        allow_task_rerun=False,
    )
    pool_uid = mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    uid = mockplan.schedule(
        target="get_imported_mtest",
        module="func_pool_base_tasks",
        path=dirname,
        kwargs=dict(name="0"),
        resource=pool_name,
        uid=uid,
        rerun=rerun_limit,
    )

    res = mockplan.run()

    assert (
        len(
            [
                worker
                for worker in mockplan.resources[pool_uid]._workers
                if worker._aborted is True
            ]
        )
        == 0
    )

    assert res.success is True
    assert mockplan.report.status == Status.PASSED
    assert pool.added_item(uid).reassign_cnt == 0


def test_schedule_from_main(mockplan):
    """
    Test scheduling Tasks from __main__ - it should not be allowed for
    ProcessPool.
    """
    # Set up a testplan and add a ProcessPool.
    pool = ProcessPool(name="ProcPool", size=2)
    mockplan.add_resource(pool)

    # First check that scheduling a Task with module string of '__main__'
    # raises the expected TaskMaterializationError.
    with pytest.raises(TaskMaterializationError):
        mockplan.schedule(
            target="target", module="__main__", resource="ProcPool"
        )

    # Secondly, check that scheduling a callable target with a __module__ attr
    # of __main__ also raises a TaskMaterializationError.
    def callable_target():
        pass

    callable_target.__module__ = "__main__"

    with pytest.raises(TaskMaterializationError):
        mockplan.schedule(target=callable_target, resource="ProcPool")


@multitest.testsuite
class SerializationSuite:
    @multitest.testcase
    def test_serialize(self, env, result):
        """Test serialization of test results."""
        # As an edge case, store a deliberately "un-pickleable" type that
        # inherits from int on the result. This should not cause an error
        # since the value should be formatted as a string.
        x = test_fields.UnPickleableInt(42)
        result.equal(
            actual=x, expected=42, description="Compare unpickleable type"
        )


def make_serialization_mtest():
    """
    Callable target to make a MultiTest containing the SerializationSuite
    defined above.
    """
    return multitest.MultiTest(
        name="SerializationMTest", suites=[SerializationSuite()]
    )


def test_serialization(mockplan):
    """Test serialization of test results."""
    pool = ProcessPool(name="ProcPool", size=2)
    mockplan.add_resource(pool)
    mockplan.schedule(
        target="make_serialization_mtest",
        module="test_pool_process",
        path=os.path.dirname(__file__),
        resource="ProcPool",
    )
    res = mockplan.run()
    assert res.success


def test_restart_worker(mockplan):
    pool_name = ProcessPool.__name__
    pool_size = 4
    retries_limit = int(pool_size / 2)

    pool = ProcessPool(
        name=pool_name,
        size=pool_size,
        worker_heartbeat=2,
        heartbeats_miss_limit=3,
        max_active_loop_sleep=1,
    )
    pool._task_retries_limit = retries_limit
    pool_uid = mockplan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    mockplan.schedule(
        target="multitest_kill_workers",
        module="func_pool_base_tasks",
        path=dirname,
        args=(os.getpid(),),
        resource=pool_name,
    )

    for idx in range(1, 25):
        mockplan.schedule(
            target="get_imported_mtest",
            module="func_pool_base_tasks",
            path=dirname,
            kwargs=dict(name=idx),
            resource=pool_name,
        )

    res = mockplan.run()

    # Check that all workers are restarted
    assert (
        len(
            [
                worker
                for worker in mockplan.resources[pool_uid]._workers
                if worker._aborted is True
            ]
        )
        == 0
    )

    assert res.run is False
    assert res.success is False
    assert mockplan.report.status == Status.ERROR
    assert mockplan.report.counter[Status.ERROR.to_json_compatible()] == 1


def test_materialization_fail(mockplan):
    """Test task target will fail to materialize in worker"""
    pool_name = ProcessPool.__name__
    pool = ProcessPool(pool_name)
    mockplan.add_resource(pool)

    @task_target
    def only_fail_under_ppool(ppid):
        if os.getpid() == ppid:
            from .func_pool_base_tasks import get_imported_mtest

            return get_imported_mtest("passing")
        raise RuntimeError("mock failure")

    mockplan.schedule(
        target=only_fail_under_ppool,
        args=(os.getpid(),),
        resource=pool_name,
    )

    res = mockplan.run()

    assert res.run is False
    assert res.success is False
    assert mockplan.report.status == Status.ERROR
    assert (
        mockplan.report.entries[0].category
        == Status.ERROR.to_json_compatible()
    )
