import shutil
import time
from itertools import permutations

import pytest

import testplan.testing.multitest as mt
from testplan.base import TestplanMock
from testplan.runners.local import LocalRunner
from testplan.runners.pools.base import Pool
from testplan.runners.pools.process import ProcessPool
from testplan.testing.base import Test
from testplan.testing.multitest.driver.base import Driver


@pytest.fixture
def plan(runpath):
    yield TestplanMock(
        name="court of testcase king",
        runpath=runpath,
        skip_strategy="tests-on-failed",
    )


@mt.testsuite
class Suite1:
    @mt.testcase
    def failed_1(self, env, result):
        result.true(False)

    @mt.testcase
    def error_1(self, env, result):
        result.true(1 + "1")

    @mt.testcase
    def passed_1(self, env, result):
        result.true(True)


@mt.testsuite
class Suite2:
    @mt.testcase
    def passed_2(self, env, result):
        result.false(False)


@mt.testsuite
class Suite3:
    def setup(self, env, result):
        "1" + 1

    @mt.testcase
    def never_3(self, env, result):
        # should never run
        import sys

        sys.exit(10)


@mt.testsuite
class Suite4:
    @mt.testcase
    def passed_4(self, env, result):
        result.false(False)

    @mt.testcase(parameters=(0, 1, 2))
    def para_4(self, env, result, p):
        result.true(p % 2 == 0)


def make_mt():
    yield mt.MultiTest("mt1", [Suite1(), Suite2()])
    yield mt.MultiTest("mt2", [Suite3(), Suite1()])
    yield mt.MultiTest("mt3", [Suite4(), Suite2()])


def descent_assert(abs_struct, group_report):
    if abs_struct is None:
        # ignore length check of case report
        return
    if isinstance(abs_struct, int):
        assert len(group_report) == abs_struct, f"error at {group_report}"
        return
    assert len(group_report) == len(abs_struct), f"error at {group_report}"
    for s, r in zip(abs_struct, group_report):
        descent_assert(s, r)


def lrunner(name, _=1):
    return LocalRunner(name)


def tpool(name, size=2):
    return Pool(name, size=size)


def ppool(name, size=2):
    return ProcessPool(name, size=size)


@pytest.mark.parametrize(
    "exec_gen, option, abs_report_struct",
    (
        (lrunner, None, ((3, 1), (1, 3), ((None, 3), 1))),
        (lrunner, "cases-on-error", ((2, 1), (1, 2), ((None, 3), 1))),
        (lrunner, "cases-on-failed", ((1, 1), (1, 1), ((None, 2), 1))),
        (lrunner, "suites-on-error", ((2,), (1,), ((None, 3), 1))),
        (lrunner, "suites-on-failed", ((1,), (1,), ((None, 2),))),
        (lrunner, "tests-on-error", ((2,),)),
        (lrunner, "tests-on-failed", ((1,),)),
        (tpool, "tests-on-error", ((2,),)),
        (tpool, "tests-on-failed", ((1,),)),
        (ppool, "tests-on-error", ((2,),)),
        (ppool, "tests-on-failed", ((1,),)),
    ),
)
def test_intra_executor(exec_gen, option, abs_report_struct, runpath):
    mockplan = TestplanMock(
        name="fast failing of functional fortress",
        runpath=runpath,
        skip_strategy=option,
    )
    mockplan.add_resource(exec_gen("exec", 1))
    for mt in make_mt():
        mockplan.schedule(target=mt, resource="exec")
    report = mockplan.run().report
    descent_assert(abs_report_struct, report)


@mt.testsuite
class Suite5:
    @mt.testcase
    def passed_5(self, env, result):
        result.true(True)

    @mt.testcase(parameters=range(int(1e4)))
    def interruptible_5(self, env, result, p):
        time.sleep(1)
        result.true(0 <= p)


@mt.testsuite
class Suite6:
    @mt.testcase
    def failed_6(self, env, result):
        time.sleep(0.5)
        result.true(False)


def make_mt2():
    yield mt.MultiTest("mt4", [Suite5()])
    yield mt.MultiTest("mt5", [Suite6()])
    yield mt.MultiTest("mt6", [Suite2(), Suite5()])


@pytest.mark.parametrize(
    "exec_ids",
    (
        *permutations(("lrunner", "tpool", "ppool"), 2),
        ("tpool", "lrunner", "tpool"),
        ("ppool", "ppool", "ppool"),
    ),
)
def test_inter_executor(exec_ids, plan):
    plan.add_resource(lrunner("lrunner"))
    plan.add_resource(tpool("tpool", 4))
    plan.add_resource(ppool("ppool", 4))
    for mt, rid in zip(make_mt2(), exec_ids):
        plan.schedule(target=mt, resource=rid)
    report = plan.run().report
    assert len(report) == 1
    assert report.entries[0].name == "mt5"


class ErrorTest(Test):
    def run(self):
        raise RuntimeError("Failing Task")


ERROR_TEST_NAME = "error_test_name"


def make_tests_with_task_error():
    yield mt.MultiTest("mt4", [Suite5()])
    yield ErrorTest(ERROR_TEST_NAME)
    yield mt.MultiTest("mt6", [Suite2(), Suite5()])


@pytest.mark.parametrize(
    "exec_ids",
    (
        *permutations(("lrunner", "tpool", "ppool"), 2),
        ("tpool", "lrunner", "tpool"),
        ("ppool", "ppool", "ppool"),
    ),
)
def test_task_error(exec_ids, plan):
    plan.add_resource(lrunner("lrunner"))
    plan.add_resource(tpool("tpool", 4))
    plan.add_resource(ppool("ppool", 4))
    for mt, rid in zip(make_tests_with_task_error(), exec_ids):
        plan.schedule(target=mt, resource=rid)
    report = plan.run().report
    assert len(report) == 1
    assert ERROR_TEST_NAME in report.entries[0].name


class SlowDriver(Driver):
    def stopping(self):
        time.sleep(2)
        super().stopping()


def test_simultaneous_discard(plan):
    plan.add_resource(tpool("tpool", 3))
    plan.schedule(
        target=mt.MultiTest("mt1", [Suite1()]),
        resource="tpool",
    )
    plan.schedule(
        target=mt.MultiTest("mt2", [Suite5()], environment=[SlowDriver("sd")]),
        resource="tpool",
    )
    plan.schedule(
        target=mt.MultiTest("mt3", [Suite5()], environment=[SlowDriver("sd")]),
        resource="tpool",
    )
    a = time.time()
    report = plan.run().report
    b = time.time()
    # runtime overhead of threadpool setup etc. should be smaller than 2
    assert b - a < 4, "multitests not discarded simultaneously"
    assert len(report) == 1
    assert report.entries[0].name == "mt1"
