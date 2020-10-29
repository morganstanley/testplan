"""TODO."""

import os

from testplan import Task
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import MultiTestConfig
from testplan.runners.pools.base import Pool, Worker
from testplan.common.utils.strings import slugify

# from testplan.common.utils.testing import log_propagation_disabled
# from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class MySuite(object):
    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath)
        assert env.runpath.endswith(slugify(env.cfg.name))


def get_mtest(name):
    return MultiTest(name="MTest{}".format(name), suites=[MySuite()])


def schedule_tests_to_pool(plan, pool, **pool_cfg):
    pool_name = pool.__name__
    pool = pool(name=pool_name, **pool_cfg)
    plan.add_resource(pool)

    dirname = os.path.dirname(os.path.abspath(__file__))

    mtest1 = MultiTest(name="MTest1", suites=[MySuite()])
    mtest2 = MultiTest(name="MTest2", suites=[MySuite()])
    uid1 = plan.schedule(target=mtest1, resource=pool_name)
    uid2 = plan.schedule(Task(target=mtest2), resource=pool_name)

    task3 = Task(target=get_mtest, path=dirname, kwargs=dict(name=3))
    uid3 = plan.schedule(task=task3, resource=pool_name)

    # Task schedule shortcut
    uid4 = plan.schedule(
        target="get_mtest",
        module="func_pool_base_tasks",
        path=dirname,
        kwargs=dict(name=4),
        resource=pool_name,
    )
    uid5 = plan.schedule(
        Task(
            target="get_mtest",
            module="func_pool_base_tasks",
            path=dirname,
            kwargs=dict(name=5),
        ),
        resource=pool_name,
    )

    from .func_pool_base_tasks import get_mtest_imported

    uid6 = plan.schedule(
        Task(target=get_mtest_imported, kwargs=dict(name=6)),
        resource=pool_name,
    )
    uid7 = plan.schedule(Task(target=get_mtest(name=7)), resource=pool_name,)

    # with log_propagation_disabled(TESTPLAN_LOGGER):
    assert plan.run().run is True

    assert plan.report.passed is True
    assert plan.report.counter == {"passed": 7, "total": 7, "failed": 0}

    names = sorted(["MTest{}".format(x) for x in range(1, 8)])
    assert sorted([entry.name for entry in plan.report.entries]) == names

    assert isinstance(plan.report.serialize(), dict)
    assert plan.result.test_results[uid1].report.name == "MTest1"
    assert plan.result.test_results[uid2].report.name == "MTest2"
    assert plan.result.test_results[uid3].report.name == "MTest3"
    assert plan.result.test_results[uid4].report.name == "MTest4"
    assert plan.result.test_results[uid5].report.name == "MTest5"
    assert plan.result.test_results[uid6].report.name == "MTest6"
    assert plan.result.test_results[uid7].report.name == "MTest7"


def test_pool_basic(mockplan):
    schedule_tests_to_pool(mockplan, Pool, size=2)


def test_pool_custom_worker(mockplan):
    class ThreadWorker(Worker):
        pass

    schedule_tests_to_pool(mockplan, Pool, worker_type=ThreadWorker, size=1)
