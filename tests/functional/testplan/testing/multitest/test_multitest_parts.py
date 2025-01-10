import re
from itertools import chain, cycle, repeat
from operator import eq

import pytest

from testplan import TestplanMock
from testplan.report import Status
from testplan.runners.pools.base import Pool as ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.testing.multitest import MultiTest, testcase, testsuite
from testplan.testing.multitest.driver import Driver


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


def test_multi_parts_duplicate_part(mocker):
    """
    Execute MultiTest parts with a part of MultiTest has been
    scheduled twice and automatically be filtered out.
    ---
    since multi_part_uid has no functional effect now, original test is invalid
    preserved for simple backward compatibility test, i.e. no exception raised
    """
    mock_warn = mocker.patch("warnings.warn")
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest_with_custom_uid(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    with pytest.raises(ValueError):
        task = Task(target=get_mtest_with_custom_uid(part_tuple=(1, 3)))
        plan.schedule(task, resource="MyThreadPool")

    assert mock_warn.call_count == 4
    assert re.search(r"remove.*multi_part_uid", mock_warn.call_args[0][0])
    assert len(plan._tests) == 3
    assert plan.run().run is True


def test_multi_parts_missing_parts():
    """
    Execute MultiTest parts while not all parts of a MultiTest are scheduled.
    It should just work now.
    """
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    pool = ThreadPool(name="MyThreadPool", size=2)
    plan.add_resource(pool)

    for idx in range(1, 3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource="MyThreadPool")

    assert plan.run().run is True

    assert len(plan.report.entries) == 1
    assert plan.report.status == Status.PASSED  # Testplan result
    assert plan.report.entries[0].name == "MTest"
    assert len(plan.report.entries[0].entries) == 2  # 2 suites
    assert plan.report.entries[0].entries[0].name == "Suite1"
    assert plan.report.entries[0].entries[1].name == "Suite2"
    assert len(plan.report.entries[0].entries[0].entries) == 1  # param group
    assert plan.report.entries[0].entries[0].entries[0].name == "test_true"
    assert len(plan.report.entries[0].entries[1].entries) == 1  # param group
    assert plan.report.entries[0].entries[1].entries[0].name == "test_false"
    assert len(plan.report.entries[0].entries[0].entries[0].entries) == 6
    assert len(plan.report.entries[0].entries[1].entries[0].entries) == 2


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


@testsuite
class Suite4:
    def setup(self, env, result):
        result.log("dummy setup")

    @testcase
    def test_single(self, env, result):
        result.true(True)

    @testcase(parameters=tuple(range(7)))
    def test_params(self, env, result, arg):
        result.gt(arg, 4)

    @testcase(parameters=tuple(range(3)), execution_group="epsilon")
    def test_params_2(self, env, result, arg):
        result.gt(arg, 1)

    def teardown(self, env, result):
        result.log("dummy teardown")


class DummyDriver(Driver):
    def starting(self):
        pass

    def stopping(self):
        pass


def test_synthesized_preserved_in_merged():
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    for i in range(4):
        if i % 2 == 0:
            plan.add(
                MultiTest(
                    "mtest",
                    [Suite1(), Suite4()],
                    environment=[DummyDriver("d")],
                    part=(i, 4),
                    before_stop=lambda env, result: result.log(
                        "dummy before_stop"
                    ),
                )
            )

    assert plan.run().run is True
    assert len(plan.report["mtest"]["Environment Start"]) == 2
    for i, e in enumerate(plan.report["mtest"]["Environment Start"]):
        assert e.uid == f"Starting - part({i * 2}/4)"

    # | p0    | p1    | p2    | p3    |
    # | ----- | ----- | ----- | ----- |
    # | s1c1  | s1c2  | s1c3  | s1c4  |
    # | s1c5  | s1c6  | s1c7  | s1c8  |
    # |       |       | s4s   | s4s   |
    # | s1c9  | s1c10 | s4c1  | s4c2  |
    # | s4s   | s4s   |       |       |
    # | s4c3  | s4c4  | s4c5  | s4c6  |
    # | s4c7  | s4c8  | s4c9  | s4c10 |
    # | s4c11 | s4t   | s4t   | s4t   |
    # | s4t   |       |       |       |
    # where
    #   s4c2 == test_params__arg_0
    #   s4c9 == test_params_2__arg_0

    s4 = plan.report["mtest"]["Suite4"]
    assert (
        s4.counter["total"] == 6
    )  # part 0, part 2 scheduled, 2 setups & 2 teardowns
    assert len(s4) == 7  # setups & teardowns not grouped, param grouped
    assert s4.entries[0].uid == "setup - part(2/4)"
    assert s4.entries[1].uid == "setup - part(0/4)"
    assert s4.entries[2].uid == "test_single"
    assert s4.entries[3].uid == "test_params"
    assert s4.entries[4].uid == "test_params_2"
    assert s4.entries[5].uid == "teardown - part(2/4)"
    assert s4.entries[6].uid == "teardown - part(0/4)"

    assert all(
        map(
            eq,
            map(lambda x: x.uid, s4.entries[3].entries),
            map(lambda x: f"test_params__arg_{x}", [1, 3, 5]),
        )
    )
    assert all(
        map(
            eq,
            map(lambda x: x.uid, s4.entries[4].entries),
            map(lambda x: f"test_params_2__arg_{x}", [0, 2]),
        )
    )

    assert len(plan.report["mtest"]["Environment Stop"]) == 4  # 2 before_stop
    es = plan.report["mtest"]["Environment Stop"]
    assert len(es) == 4
    assert es.entries[0].uid == "Before Stop - part(2/4)"
    assert es.entries[1].uid == "Stopping - part(2/4)"
    assert es.entries[2].uid == "Before Stop - part(0/4)"
    assert es.entries[3].uid == "Stopping - part(0/4)"


@testsuite
class Suite5:
    def teardown(self, env, result):
        result.log("padding")

    @testcase
    def c1(self, env, result):
        result.true(True)


@testsuite
class Suite6:
    @testcase
    def c1(self, env, result):
        result.false(True)

    @testcase
    def c2(self, env, result):
        result.true(False)


@testsuite
class Suite7:
    @testcase
    def c1(self, env, result):
        result.false(False)

    @testcase
    def c2(self, env, result):
        result.false(False)

    @testcase
    def c3(self, env, result):
        result.false(False)


def test_order_maintained_w_synthesized_in_merged():
    plan = TestplanMock(name="plan", merge_scheduled_parts=True)
    for i in range(3):
        plan.add(
            MultiTest(
                "mtest",
                [Suite5(), Suite6(), Suite7()],
                part=(i, 3),
            )
        )

    assert plan.run().run is True

    # | p0    | p1    | p2    |
    # | ----- | ----- | ----- |
    # | s5c1  | s6c1  | sbc2  |
    # | s5t   |       |       |
    # | s7c1  | s7c2  | s7c3  |

    # round-robin without collation will result in order [s7c2, s7c3, s7c1]

    s7 = plan.report["mtest"]["Suite7"]
    assert s7.entries[0].uid == "c1"
    assert s7.entries[1].uid == "c2"
    assert s7.entries[2].uid == "c3"
