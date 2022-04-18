"""TODO."""

import os

from testplan import Task
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import MultiTestConfig
from testplan.runners.pools.base import Pool, Worker
from testplan.common.utils.strings import slugify


@testsuite
class MySuite:
    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")
        assert isinstance(env.parent.cfg, MultiTestConfig)
        assert os.path.exists(env.parent.runpath)
        assert env.parent.runpath.endswith(slugify(env.parent.cfg.name))


def get_mtest(name):
    return MultiTest(name="MTest{}".format(name), suites=[MySuite()])


def schedule_tests_to_pool(plan, pool, **pool_cfg):
    pool_name = pool.__name__
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)
    uids = []

    dirname = os.path.dirname(os.path.abspath(__file__))

    mtest1 = MultiTest(name="MTest1", suites=[MySuite()])
    mtest2 = MultiTest(name="MTest2", suites=[MySuite()])
    uids.append(plan.schedule(target=mtest1, weight=1, resource=pool_name))

    uids.append(
        plan.schedule(Task(target=mtest2, weight=2), resource=pool_name)
    )

    task3 = Task(target=get_mtest, path=dirname, kwargs=dict(name=3), weight=3)
    uids.append(plan.schedule(task=task3, resource=pool_name))

    # Task schedule shortcut
    uids.append(
        plan.schedule(
            target="get_mtest",
            module="func_pool_base_tasks",
            path=dirname,
            kwargs=dict(name=4),
            weight=4,
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(
                target="get_mtest",
                module="func_pool_base_tasks",
                path=dirname,
                kwargs=dict(name=5),
                weight=5,
            ),
            resource=pool_name,
        )
    )

    from .func_pool_base_tasks import get_mtest_imported

    uids.append(
        plan.schedule(
            Task(target=get_mtest_imported, kwargs=dict(name=6), weight=6),
            resource=pool_name,
        )
    )
    uids.append(
        plan.schedule(
            Task(target=get_mtest(name=7), weight=7), resource=pool_name
        )
    )

    assert plan.run().run is True

    assert plan.report.passed is True
    assert plan.report.counter == {"passed": 10, "total": 10, "failed": 0}

    names = ["MTest{}".format(x) for x in range(1, 8)]
    assert [entry.name for entry in plan.report.entries] == names

    assert isinstance(plan.report.serialize(), dict)
    assert [plan.result.test_results[uid].report.name for uid in uids] == names
    assert list(pool._executed_tests) == uids[::-1]

    assert not pool.is_alive
    assert not any(worker.is_alive for worker in pool._workers)


def test_pool_basic(mockplan):
    schedule_tests_to_pool(mockplan, Pool, size=2)


def test_pool_custom_worker(mockplan):
    class ThreadWorker(Worker):
        pass

    schedule_tests_to_pool(mockplan, Pool, worker_type=ThreadWorker, size=1)
