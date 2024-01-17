import itertools

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.runners.pools.base import Pool as ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.common.report.base import Status


@testsuite
class Suite1:
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(10)))
    def test_true(self, env, result, val):
        result.true(val, description="Check if value is true")


@testsuite
class Suite2:
    """A test suite with parameterized testcases."""

    @testcase(parameters=(False, None, ""))
    def test_false(self, env, result, val):
        result.false(val, description="Check if value is false")


@testsuite
class Suite3:
    """A test suite with parameterized testcases."""

    @testcase(parameters=(1, -1))
    def test_not_equal(self, env, result, val):
        result.not_equal(0, val, description="Check if values are not equal")


class MockMultiTest(MultiTest):
    """A Multitest mock that creates test result with exception caught."""

    def _post_run_checks(self, start_threads, start_procs):
        super(MockMultiTest, self)._post_run_checks(start_threads, start_procs)
        if self.cfg.part[0] % 2 == 0:
            raise RuntimeError("Deliberately raises")


uid_gen = itertools.cycle([i for i in range(10)])


def get_mtest(part_tuple=None):
    return MultiTest(
        name="MTest", suites=[Suite1(), Suite2()], part=part_tuple
    )


def get_mtest_with_custom_uid(part_tuple=None):
    return MultiTest(
        name="MTest",
        suites=[Suite1(), Suite2()],
        part=part_tuple,
        multi_part_uid=lambda name, part: "{} - {}".format(
            name, next(uid_gen)
        ),
    )


def test_multi_parts_not_merged():
    """Execute MultiTest parts but do not merge reports."""
    plan = TestplanMock(name="plan", merge_scheduled_parts=False)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    assert plan.run().run is True

    assert len(plan.report.entries) == 3
    assert plan.report.entries[0].name == "MTest - part(0/3)"
    assert plan.report.entries[1].name == "MTest - part(1/3)"
    assert plan.report.entries[2].name == "MTest - part(2/3)"
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
    """
    Schedule MultiTest parts in different ways, execute them and merge reports.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    def _get_mtest():
        return MultiTest(
            name="MTest", suites=[Suite1(), Suite2()], part=(2, 3)
        )

    plan.add(target=_get_mtest())  # local_runner
    plan.add(Task(target=get_mtest(part_tuple=(1, 3))))  # local_runner
    plan.schedule(
        Task(target=get_mtest(part_tuple=(0, 3))), resource="MyThreadPool"
    )

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


def test_multi_parts_incorrect_schedule():
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

    assert len(plan._tests) == 5

    assert plan.run().run is False

    assert len(plan.report.entries) == 6  # one placeholder report & 5 siblings
    assert len(plan.report.entries[0].entries) == 0  # already cleared
    assert plan.report.status == Status.ERROR  # Testplan result
    assert (
        "invalid parameter of part provided"
        in plan.report.entries[0].logs[0]["message"]
    )


def test_multi_parts_duplicate_part():
    """
    Execute MultiTest parts with a part of MultiTest has been
    scheduled twice and automatically be filtered out.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest_with_custom_uid(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    task = Task(target=get_mtest_with_custom_uid(part_tuple=(1, 3)))
    plan.schedule(task, resource="MyThreadPool")

    assert len(plan._tests) == 4

    assert plan.run().run is False

    assert len(plan.report.entries) == 5  # one placeholder report & 4 siblings
    assert len(plan.report.entries[0].entries) == 0  # already cleared
    assert plan.report.status == Status.ERROR  # Testplan result
    assert (
        "duplicate MultiTest parts had been scheduled"
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

    assert plan.run().run is False

    assert len(plan.report.entries) == 3  # one placeholder report & 2 siblings
    assert len(plan.report.entries[0].entries) == 0  # already cleared
    assert plan.report.status == Status.ERROR  # Testplan result
    assert (
        "not all MultiTest parts had been scheduled"
        in plan.report.entries[0].logs[0]["message"]
    )


def test_multi_parts_not_successfully_executed():
    """
    Any part did not run successfully then parts cannot be merged
    and error will be logged.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    plan.add(MockMultiTest(name="MTest", suites=[Suite1()], part=(0, 2)))
    plan.add(MockMultiTest(name="MTest", suites=[Suite1()], part=(1, 2)))

    assert plan.run().run is False

    assert len(plan.report.entries) == 3  # one placeholder report & 2 siblings
    assert len(plan.report.entries[0].entries) == 0  # already cleared
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # 1st part raised
    assert "Deliberately raises" in plan.report.entries[0].logs[0]["message"]
