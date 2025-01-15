"""TODO."""

import os

from testplan import Task
from testplan.common.utils.path import fix_home_prefix
from testplan.common.utils.strings import slugify
from testplan.runners.pools.base import Pool, Worker
from testplan.testing.multitest import MultiTest, testcase, testsuite
from testplan.testing.multitest.base import MultiTestConfig


@testsuite
class MyLocalSuite:
    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")
        assert isinstance(env.parent.cfg, MultiTestConfig)
        assert os.path.exists(env.parent.runpath)
        assert env.parent.runpath.endswith(slugify(env.parent.cfg.name))


def get_mtest(name):

    # Nested function won't be serialized by pickle.
    def nested_before_start(env):
        pass

    def nested_after_stop(env):
        pass

    return MultiTest(
        name="MTest{}".format(name),
        suites=[MyLocalSuite()],
        before_start=nested_before_start,
        after_stop=nested_after_stop,
    )


def schedule_tests_to_pool(plan, pool, schedule_path=None, **pool_cfg):
    pool_name = pool.__name__
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)
    uids = []

    if schedule_path is None:
        schedule_path = fix_home_prefix(
            os.path.dirname(os.path.abspath(__file__))
        )

    mtest1 = MultiTest(name="MTest1", suites=[MyLocalSuite()])
    mtest2 = MultiTest(name="MTest2", suites=[MyLocalSuite()])
    uids.append(plan.schedule(target=mtest1, weight=1, resource=pool_name))

    uids.append(
        plan.schedule(Task(target=mtest2, weight=2), resource=pool_name)
    )

    task3 = Task(target=get_mtest, kwargs=dict(name=3), weight=3)
    uids.append(plan.schedule(task=task3, resource=pool_name))

    # Task schedule shortcut
    uids.append(
        plan.schedule(
            target="get_imported_mtest",
            module="func_pool_base_tasks",
            path=schedule_path,
            kwargs=dict(name=4),
            weight=4,
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(
                target="get_imported_mtest",
                module="func_pool_base_tasks",
                path=schedule_path,
                kwargs=dict(name=5),
                weight=5,
            ),
            resource=pool_name,
        )
    )

    from .func_pool_base_tasks import get_imported_mtest

    uids.append(
        plan.schedule(
            Task(target=get_imported_mtest, kwargs=dict(name=6), weight=6),
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(target=get_mtest(name=7), weight=7), resource=pool_name
        )
    )

    # This returned class won't be serialized by pickle.
    uids.append(
        plan.schedule(
            Task(target=get_imported_mtest(name=8), weight=8),
            resource=pool_name,
        )
    )

    assert plan.run().run is True

    assert plan.report.passed is True
    assert plan.report.counter == {"passed": 12, "total": 12, "failed": 0}

    names = ["MTest{}".format(x) for x in range(1, 9)]
    assert [entry.name for entry in plan.report.entries] == names

    assert isinstance(plan.report.serialize(), dict)
    assert [plan.result.test_results[uid].report.name for uid in uids] == names
    assert list(pool._executed_tests) == uids[::-1]

    # All tasks assigned once
    for uid in pool._task_retries_cnt:
        assert pool._task_retries_cnt[uid] == 0
        assert pool.added_item(uid).reassign_cnt == 0

    # Check attachment exists in local
    assert os.path.exists(
        plan.report.entries[7].entries[0].entries[1].entries[0]["source_path"]
    )

def schedule_tests_to_remote_pool_on_specific_worker(plan, pool, schedule_path=None, **pool_cfg):
    pool_name = pool.__name__
    host1, host2 = (pool_cfg.get("hosts").keys())
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)
    uids = []

    if schedule_path is None:
        schedule_path = fix_home_prefix(
            os.path.dirname(os.path.abspath(__file__))
        )

    mtest1 = MultiTest(name="MTest1", suites=[MyLocalSuite()])
    mtest2 = MultiTest(name="MTest2", suites=[MyLocalSuite()])
    task1 = Task(target=mtest1, weight=1, resource=pool_name, workers_name={host1})
    uids.append(
        plan.schedule(task1)
    )

    task2 = Task(target=mtest2, weight=2, resource=pool_name, workers_name={host2})
    uids.append(
        plan.schedule(task2)
    )

    # Task schedule shortcut
    uids.append(
        plan.schedule(
            target="get_imported_mtest",
            module="func_pool_base_tasks",
            path=schedule_path,
            kwargs=dict(name=4),
            weight=4,
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(
                target="get_imported_mtest",
                module="func_pool_base_tasks",
                path=schedule_path,
                kwargs=dict(name=5),
                weight=5,
            ),
            resource=pool_name,
        )
    )

    from .func_pool_base_tasks import get_imported_mtest

    uids.append(
        plan.schedule(
            Task(target=get_imported_mtest, kwargs=dict(name=6), weight=6),
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(target=get_mtest(name=7), weight=7), resource=pool_name
        )
    )

    # This returned class won't be serialized by pickle.
    uids.append(
        plan.schedule(
            Task(target=get_imported_mtest(name=8), weight=8),
            resource=pool_name,
        )
    )

    assert plan.run().run is True

    assert plan.report.passed is True
    assert plan.report.counter == {"passed": 12, "total": 12, "failed": 0}

    names = ["MTest{}".format(x) for x in range(1, 9)]
    assert [entry.name for entry in plan.report.entries] == names

    assert isinstance(plan.report.serialize(), dict)
    assert [plan.result.test_results[uid].report.name for uid in uids] == names
    assert list(pool._executed_tests) == uids[::-1]

    # All tasks assigned once
    for uid in pool._task_retries_cnt:
        assert pool._task_retries_cnt[uid] == 0
        assert pool.added_item(uid).reassign_cnt == 0

    # Check attachment exists in local
    assert os.path.exists(
        plan.report.entries[7].entries[0].entries[1].entries[0]["source_path"]
    )

    for task in [task1, task2]:
        for pool_name, executors in task.executors.items():
            for executor in executors:
                assert executor in task.workers_name


def test_pool_basic(mockplan):
    schedule_tests_to_pool(mockplan, Pool, size=2)


def test_pool_custom_worker(mockplan):
    class ThreadWorker(Worker):
        pass

    schedule_tests_to_pool(mockplan, Pool, worker_type=ThreadWorker, size=1)
