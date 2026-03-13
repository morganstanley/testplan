import re
from itertools import chain, cycle, repeat
from operator import eq

import pytest

from testplan import TestplanMock
from testplan.report import Status
from testplan.runners.pools.base import Pool as ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.testing.multitest import MultiTest, testcase, testsuite


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


def get_mtest(part_tuple=None):
    return MultiTest(
        name="MTest", suites=[Suite1(), Suite2()], part=part_tuple
    )


uid_gen = cycle([i for i in range(10)])


def get_mtest_with_custom_uid(part_tuple=None):
    # NOTE: multi_part_uid is noop now
    return MultiTest(
        name="MTest",
        suites=[Suite1(), Suite2()],
        part=part_tuple,
        multi_part_uid=lambda name, part: "{} - {}".format(
            name, next(uid_gen)
        ),
    )


def test_multi_parts():
    """Execute MultiTest parts"""
    plan = TestplanMock(name="plan")
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


def test_multi_parts_incorrect_schedule():
    """
    Execute MultiTest parts with a MultiTest scheduled twice with
    different part splits. Without merge, all parts appear separately
    and no error is raised.
    """
    plan = TestplanMock(name="plan")
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    for idx in range(2):
        task = Task(target=get_mtest(part_tuple=(idx, 2)))
        plan.schedule(task, resource="MyThreadPool")

    assert len(plan._tests) == 5

    assert plan.run().run is True

    assert len(plan.report.entries) == 5
    assert plan.report.status == Status.FAILED


def test_multi_parts_missing_parts():
    """
    Execute MultiTest parts while not all parts of a MultiTest are scheduled.
    Without merge, the scheduled parts just appear separately.
    """
    plan = TestplanMock(name="plan")
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(1, 3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    assert plan.run().run is True

    assert len(plan.report.entries) == 2
    assert plan.report.status == Status.PASSED
    assert plan.report.entries[0].name == "MTest - part(1/3)"
    assert plan.report.entries[1].name == "MTest - part(2/3)"


def test_multi_parts_not_successfully_executed():
    """
    A part that did not run successfully shows as a separate entry
    with an error status. Each part is independent.
    """
    plan = TestplanMock(name="plan")
    plan.add(MockMultiTest(name="MTest", suites=[Suite1()], part=(0, 2)))
    plan.add(MockMultiTest(name="MTest", suites=[Suite1()], part=(1, 2)))

    assert plan.run().run is False

    assert len(plan.report.entries) == 2
    assert plan.report.status == Status.FAILED


def test_even_parts():
    plan = TestplanMock(name="plan")
    for i in range(8):
        plan.add(
            MultiTest(
                name="MTest",
                suites=[Suite1(), Suite2(), Suite3()],
                part=(i, 8),
            )
        )

    assert plan.run().run is True
    assert all(
        map(
            eq,
            map(lambda e: e.counter["total"], plan.report.entries),
            chain(repeat(2, 7), repeat(1)),
        )
    )
    assert all(
        map(eq, map(len, plan.report.entries), [1, 1, 2, 2, 2, 2, 2, 1])
    )
    for i in range(8):
        assert plan.report.entries[i].entries[0].name == "Suite1"
    for i in range(2, 5):
        assert plan.report.entries[i].entries[1].name == "Suite2"
    for i in range(5, 7):
        assert plan.report.entries[i].entries[1].name == "Suite3"
