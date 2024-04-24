import inspect
import sys

import testplan.testing.multitest.suite as suite
from testplan import TestplanMock
from testplan.testing.multitest import MultiTest
from tests.unit.testplan.testing.test_pytest import pytest_test_inst


@suite.testsuite
class OneSuite:
    @suite.testcase
    def passing(self, env, result):
        result.true(True)

    @suite.testcase
    def failing(self, env, result):
        result.true(False)

    @suite.testcase
    @suite.xfail(reason="coding after drinking")
    def expect_to_fail(self, env, result):
        result.true(False)


@suite.testsuite
class AnotherSuite:
    @suite.testcase(parameters={"b": [True, False]}, execution_group="PAR")
    def with_param(self, env, result, b):
        result.true(b)

    @suite.skip_if(lambda testsuite: True)
    @suite.testcase
    def should_skip(self, env, result):
        result.true(False)

    @suite.testcase
    def result_skip_should_skip(self, env, result):
        result.true(True)
        result.skip("haha")

    # NOTE: we cannot put "xfail" above "testcase" since it's a parametrized case
    # NOTE: we might need to fix this behaviour...
    @suite.testcase(parameters={"b": [True, False, None]})
    @suite.xfail(reason="coding after drinking again", strict=True)
    def strictly_expect_to_fail(self, env, result, b):
        result.true(b)


@suite.skip_if_testcase(lambda testsuite: True)
@suite.testsuite
class SkippedSuite:
    @suite.testcase
    def should_skip_jr(self, env, result):
        sys.exit(1)


def test_multitest_report_filter_passed():
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        reporting_filter="P",
    )
    plan.add(MultiTest(name="TestMT", suites=[OneSuite(), AnotherSuite()]))
    mt_report = plan.run().report["TestMT"]

    assert len(mt_report) == 4
    assert len(mt_report["OneSuite"]) == 1
    assert mt_report["OneSuite"]["passing"]
    assert len(mt_report["AnotherSuite"]["with_param"]) == 1
    assert mt_report["AnotherSuite"]["with_param"]["with_param__b_True"]


def test_multitest_report_filter_passed_or_xfail():
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        reporting_filter="PA",
    )
    plan.add(
        MultiTest(
            name="TestMT", suites=[OneSuite(), AnotherSuite(), SkippedSuite()]
        )
    )
    mt_report = plan.run().report["TestMT"]

    assert len(mt_report) == 4
    assert len(mt_report["OneSuite"]) == 2
    assert mt_report["OneSuite"]["expect_to_fail"]
    assert len(mt_report["AnotherSuite"]) == 2
    assert len(mt_report["AnotherSuite"]["strictly_expect_to_fail"]) == 2
    assert mt_report["AnotherSuite"]["strictly_expect_to_fail"][
        "strictly_expect_to_fail__b_False"
    ]
    assert mt_report["AnotherSuite"]["strictly_expect_to_fail"][
        "strictly_expect_to_fail__b_None"
    ]


def test_multitest_report_filter_not_passed_and_not_failed():
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        reporting_filter="pf",
    )
    plan.add(
        MultiTest(
            name="TestMT", suites=[OneSuite(), AnotherSuite(), SkippedSuite()]
        )
    )
    mt_report = plan.run().report["TestMT"]

    assert len(mt_report) == 3
    assert len(mt_report["OneSuite"]) == 1
    assert mt_report["OneSuite"]["expect_to_fail"]
    assert len(mt_report["AnotherSuite"]) == 3
    assert mt_report["AnotherSuite"]["should_skip"]
    assert mt_report["AnotherSuite"]["result_skip_should_skip"]
    assert len(mt_report["AnotherSuite"]["strictly_expect_to_fail"]) == 3
    assert mt_report["AnotherSuite"]["strictly_expect_to_fail"][
        "strictly_expect_to_fail__b_True"
    ]
    assert mt_report["AnotherSuite"]["strictly_expect_to_fail"][
        "strictly_expect_to_fail__b_False"
    ]
    assert mt_report["AnotherSuite"]["strictly_expect_to_fail"][
        "strictly_expect_to_fail__b_None"
    ]
    assert len(mt_report["SkippedSuite"]) == 1
    assert mt_report["SkippedSuite"]["should_skip_jr"]


def test_pytest_report_filter_not_skipped(pytest_test_inst):
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        reporting_filter="s",
    )
    plan.schedule(pytest_test_inst)
    pt_report = plan.run().report["My PyTest"]

    assert (
        pt_report["pytest_tests.py::TestPytestMarks"].entries[0].name
        != "test_skipped"
    )
