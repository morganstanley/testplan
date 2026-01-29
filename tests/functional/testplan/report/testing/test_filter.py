import inspect
import sys

import testplan.testing.multitest.suite as suite
from testplan import TestplanMock
from testplan.common.utils.testing import argv_overridden
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.base import Driver
from tests.unit.testplan.testing.test_pytest import pytest_test_inst


class DummyDriver(Driver):
    pass


@suite.testsuite
class OneSuite:
    @suite.testcase
    def passing(self, env, result):
        result.true(True)

    @suite.testcase
    def failing(self, env, result):
        result.true(True)
        result.true(False)

    @suite.testcase
    @suite.xfail(reason="coding after drinking")
    def expect_to_fail(self, env, result):
        result.true(True)
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
        reporting_exclude_filter="EFIUXSABC",
    )
    plan.add(MultiTest(name="TestMT", suites=[OneSuite(), AnotherSuite()]))
    mt_report = plan.run().report["TestMT"]

    assert len(mt_report) == 2
    assert len(mt_report["OneSuite"]) == 1
    assert mt_report["OneSuite"]["passing"]
    assert len(mt_report["AnotherSuite"]["with_param"]) == 1
    assert mt_report["AnotherSuite"]["with_param"]["with_param__b_True"]


def test_multitest_report_filter_passed_or_xfail():
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        reporting_exclude_filter="EFIUXSBC",
    )
    plan.add(
        MultiTest(
            name="TestMT", suites=[OneSuite(), AnotherSuite(), SkippedSuite()]
        )
    )
    mt_report = plan.run().report["TestMT"]

    assert len(mt_report) == 2
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
        reporting_exclude_filter="PF",
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
        reporting_exclude_filter="S",
    )
    plan.schedule(pytest_test_inst)
    pt_report = plan.run().report["My PyTest"]

    assert (
        pt_report["pytest_tests.py::TestPytestMarks"].entries[0].name
        != "test_skipped"
    )


def _do_assert(exp_structure, mt_report):
    for i, i_ in exp_structure.items():
        assert len(mt_report[i]) == len(i_)
        for j, j_ in i_.items():
            if isinstance(j_, int):
                assert len(mt_report[i][j]) == j_
            else:
                assert len(mt_report[i][j]) == len(j_)
                for k, k_ in j_.items():
                    assert len(mt_report[i][j][k]) == k_


def test_mt_omit_passed():
    with argv_overridden("--omit-passed", "--driver-info"):
        plan = TestplanMock(
            name=f"{inspect.currentframe().f_code.co_name}_test",
            parse_cmdline=True,
        )
        plan.add(
            MultiTest(
                name="TestMT",
                suites=[OneSuite(), AnotherSuite(), SkippedSuite()],
                environment=[DummyDriver(name="a"), DummyDriver(name="b")],
            )
        )
        mt_report = plan.run().report["TestMT"]

    exp_structure = {
        "Environment Start": {"Starting": 3},
        "OneSuite": {"passing": 0, "failing": 2, "expect_to_fail": 2},
        "AnotherSuite": {
            "with_param": {
                "with_param__b_True": 0,
                "with_param__b_False": 1,
            },
            "should_skip": 1,
            "result_skip_should_skip": 2,
            "strictly_expect_to_fail": {
                "strictly_expect_to_fail__b_True": 1,
                "strictly_expect_to_fail__b_False": 1,
                "strictly_expect_to_fail__b_None": 1,
            },
        },
        "SkippedSuite": {"should_skip_jr": 1},
        "Environment Stop": {"Stopping": 2},
    }

    _do_assert(exp_structure, mt_report)


def test_mt_preserve_structure():
    with argv_overridden("--report-exclude=efpiuxc", "--driver-info"):
        plan = TestplanMock(
            name=f"{inspect.currentframe().f_code.co_name}_test",
            parse_cmdline=True,
        )
        plan.add(
            MultiTest(
                name="TestMT",
                suites=[OneSuite(), AnotherSuite(), SkippedSuite()],
                environment=[DummyDriver(name="a"), DummyDriver(name="b")],
            )
        )
        mt_report = plan.run().report["TestMT"]

    exp_structure = {
        "Environment Start": {"Starting": 3},
        "OneSuite": {"passing": 0, "failing": 0, "expect_to_fail": 2},
        "AnotherSuite": {
            "with_param": {
                "with_param__b_True": 0,
                "with_param__b_False": 0,
            },
            "should_skip": 1,
            "result_skip_should_skip": 2,
            "strictly_expect_to_fail": {
                "strictly_expect_to_fail__b_True": 0,
                "strictly_expect_to_fail__b_False": 1,
                "strictly_expect_to_fail__b_None": 1,
            },
        },
        "SkippedSuite": {"should_skip_jr": 1},
        "Environment Stop": {"Stopping": 2},
    }

    _do_assert(exp_structure, mt_report)


def test_mt_assign_error_not_filtered():
    from testplan.runners.pools.base import Pool

    class CustomPool(Pool):
        def _can_assign_task(self, _):
            return False

    def _dummy_mt_2():
        return MultiTest(
            name="TestMT2",
            suites=[OneSuite()],
        )

    with argv_overridden("--omit-passed"):
        plan = TestplanMock(
            name=f"{inspect.currentframe().f_code.co_name}_test",
            parse_cmdline=True,
        )
        plan.add_resource(CustomPool(name="pool", size=1))
        plan.add(
            MultiTest(
                name="TestMT",
                suites=[OneSuite()],
            )
        )
        plan.schedule(target=_dummy_mt_2, resource="pool")
        report = plan.run().report

    assert len(report) == 2
    assert len(report["TestMT"]) == 1
    assert len(report["TestMT"]["OneSuite"]["passing"]) == 0  # filtered
    assert len(report["TestMT"]["OneSuite"]["failing"]) == 2
    assert len(report["TestMT"]["OneSuite"]["expect_to_fail"]) == 2

    assert report.entries[1].name == "TestMT2"
    assert len(report.entries[1].entries) == 0
