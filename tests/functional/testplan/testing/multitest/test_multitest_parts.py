from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.runners.pools import ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.report import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class Suite1(object):
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(10)))
    def test_true(self, env, result, val):
        result.true(val, description="Check if value is true")


@testsuite
class Suite2(object):
    """A test suite with parameterized testcases."""

    @testcase(parameters=(False, True, None))
    def test_false(self, env, result, val):
        result.false(val, description="Check if value is false")


@testsuite
class Suite3(object):
    """A test suite with parameterized testcases."""

    @testcase(parameters=(1, -1))
    def test_not_equal(self, env, result, val):
        result.not_equal(0, val, description="Check if values are not equal")


def get_mtest(part_tuple=None):
    test = MultiTest(
        name="MTest", suites=[Suite1(), Suite2()], part=part_tuple
    )
    return test


def test_multi_parts_not_merged():
    """Execute MultiTest parts but do not merge report."""
    plan = TestplanMock(name="plan", merge_scheduled_parts=False)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    assert len(plan.report.entries) == 3
    assert plan.report.entries[0].name == "MTest - part(1/3)"
    assert plan.report.entries[1].name == "MTest - part(2/3)"
    assert plan.report.entries[2].name == "MTest - part(3/3)"
    assert len(plan.report.entries[0].entries) == 2  # 2 suites
    assert plan.report.entries[0].entries[0].name == "Suite1"
    assert plan.report.entries[0].entries[1].name == "Suite2"
    assert len(plan.report.entries[0].entries[0].entries) == 1  # param group
    assert plan.report.entries[0].entries[0].entries[0].name == "test_true"
    assert len(plan.report.entries[0].entries[1].entries) == 1  # param group
    assert plan.report.entries[0].entries[1].entries[0].name == "test_false"
    assert len(plan.report.entries[0].entries[0].entries[0].entries) == 4
    assert len(plan.report.entries[0].entries[1].entries[0].entries) == 1


def test_multi_parts_merged():
    """Execute MultiTest parts and merge report."""
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    assert len(plan.report.entries) == 1
    assert plan.report.entries[0].name == "MTest"
    assert len(plan.report.entries[0].entries) == 2  # 2 suites
    assert plan.report.entries[0].entries[0].name == "Suite1"
    assert plan.report.entries[0].entries[1].name == "Suite2"
    assert len(plan.report.entries[0].entries[0].entries) == 1  # param group
    assert plan.report.entries[0].entries[0].entries[0].name == "test_true"
    assert len(plan.report.entries[0].entries[1].entries) == 1  # param group
    assert plan.report.entries[0].entries[1].entries[0].name == "test_false"
    assert len(plan.report.entries[0].entries[0].entries[0].entries) == 10
    assert len(plan.report.entries[0].entries[1].entries[0].entries) == 3


def test_multi_parts_invalid_parameter_1():
    """
    Execute MultiTest parts with invalid parameters that a part
    of MultiTest has been scheduled twice.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")
    plan.schedule(
        Task(target=get_mtest(part_tuple=(1, 3))), resource="MyThreadPool"
    )

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.UNKNOWN  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.UNKNOWN  # Suite2
    assert (
        "duplicate MultiTest parts had been scheduled"
        in plan.report.entries[0].logs[0]["message"]
    )


def test_multi_parts_invalid_parameter_2():
    """
    Execute MultiTest parts with invalid parameters that a MultiTest
    has been scheduled twice and each time split into different parts.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")
    for idx in range(2):
        task = Task(target=get_mtest(part_tuple=(idx, 2)))
        plan.schedule(task, resource="MyThreadPool")

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.UNKNOWN  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.UNKNOWN  # Suite2
    assert (
        "invalid parameter of part provided"
        in plan.report.entries[0].logs[0]["message"]
    )


def test_multi_parts_missing_parts():
    """
    Execute MultiTest parts with invalid parameters that
    not all parts of a MultiTest are scheduled.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(1, 3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.UNKNOWN  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.UNKNOWN  # Suite2
    assert (
        "not all MultiTest parts had been scheduled"
        in plan.report.entries[0].logs[0]["message"]
    )


def test_multi_parts_duplicate_names():
    """
    The name of schedule MultiTest part objects is duplicate as another one
    thus an exception will be raised.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    plan.add(MultiTest(name="MTest", suites=[Suite3()]))

    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(1, 3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 1
    assert plan.report.status == Status.PASSED  # Testplan result
    assert plan.report.entries[0].status == Status.PASSED  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.PASSED  # Suite3

    exc = plan.result.step_results["_create_result"]
    assert isinstance(exc, ValueError)
    assert "MTest already exists" in str(exc)
