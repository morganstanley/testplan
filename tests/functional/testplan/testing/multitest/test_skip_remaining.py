import pytest

import testplan.testing.common as common
import testplan.testing.multitest as mt
from testplan.base import TestplanMock


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
    # NOTE: ``stop_on_error`` default value to be changed to ``False``
    yield mt.MultiTest("mt1", [Suite1(), Suite2()], stop_on_error=False)
    yield mt.MultiTest("mt2", [Suite3(), Suite1()], stop_on_error=False)
    yield mt.MultiTest("mt3", [Suite4(), Suite2()], stop_on_error=False)


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


@pytest.mark.parametrize(
    "cli_arg,abs_report_struct",
    (
        (None, ((3, 1), (1, 3), ((None, 3), 1))),
        ("cases-on-error", ((2, 1), (1, 2), ((None, 3), 1))),
        ("cases-on-failed", ((1, 1), (1, 1), ((None, 2), 1))),
        ("suites-on-error", ((2,), (1,), ((None, 3), 1))),
        ("suites-on-failed", ((1,), (1,), ((None, 2),))),
        ("tests-on-error", ((2,),)),
        ("tests-on-failed", ((1,),)),
    ),
)
def test_skip_remaining_intra_executor(cli_arg, abs_report_struct):
    mockplan = TestplanMock(
        name="in the middle of functional test",
        skip_strategy=common.SkipStrategy.from_option(cli_arg)
        if cli_arg
        else None,
    )
    for mt in make_mt():
        mockplan.add(mt)
    report = mockplan.run().report
    descent_assert(abs_report_struct, report)
