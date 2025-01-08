import os
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.base import Driver

from testplan.common.utils.testing import check_report
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    Status,
)


@testsuite
class MySuite:
    @testcase
    def passed_test(self, env, result):
        pass


@testsuite
class RaisingSuite:
    def pre_testcase(self, name, env, result):
        raise Exception("Exception raised!")

    @testcase
    def passed_test(self, env, result):
        pass


@testsuite
class FailingSuite:
    @testcase
    def failed_test(self, env, result):
        result.fail("Failed test")


class RaisingStartDriver(Driver):
    def starting(self):
        print("Starting environment!")
        raise Exception("Exception raised!")


def raising_hook(env, result):
    raise Exception("Exception raised!")


def passed_hook(env, result):
    result.equal(1, 1, description="sample assertion")


def error_handler_fn(env, result):
    result.log("Error handler ran!")


def test_driver_failure(mockplan):
    multitest = MultiTest(
        name="MyMultitest",
        suites=[MySuite()],
        environment=[
            RaisingStartDriver("RaisingStart"),
        ],
        error_handler=error_handler_fn,
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestGroupReport(
        name="Error Handler",
        category=ReportCategories.SYNTHESIZED,
        entries=[
            TestCaseReport(
                name="error_handler_fn",
                entries=[
                    {
                        "description": "Error handler ran!",
                        "type": "Log",
                    }
                ],
            ),
        ],
    )

    assert mockplan.report.status == Status.ERROR
    assert mockplan.report.entries[0].status == Status.ERROR
    check_report(expected_report, mockplan.report.entries[0].entries[2])


def test_suite_hook_failure(mockplan):
    multitest = MultiTest(
        name="MyMultitest",
        suites=[RaisingSuite()],
        error_handler=error_handler_fn,
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MyMultitest",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="RaisingSuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="passed_test",
                                entries=[],
                                status_override=Status.ERROR,
                            )
                        ],
                        tags=None,
                    ),
                    TestGroupReport(
                        name="Error Handler",
                        category=ReportCategories.SYNTHESIZED,
                        entries=[
                            TestCaseReport(
                                name="error_handler_fn",
                                entries=[
                                    {
                                        "description": "Error handler ran!",
                                        "type": "Log",
                                    }
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    assert mockplan.report.status == Status.ERROR
    assert mockplan.report.entries[0].status == Status.ERROR
    assert mockplan.report.entries[0].entries[1].status == Status.PASSED
    check_report(expected_report, mockplan.report)


def test_multitest_hook_failure(mockplan):
    multitest = MultiTest(
        name="MyMultitest",
        suites=[MySuite()],
        after_start=raising_hook,
        error_handler=error_handler_fn,
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MyMultitest",
                category=ReportCategories.MULTITEST,
                status_override=Status.ERROR,
                entries=[
                    TestGroupReport(
                        name="Environment Start",
                        category=ReportCategories.SYNTHESIZED,
                        entries=[
                            TestCaseReport(
                                name="After Start",
                                entries=[],
                                status_override=Status.ERROR,
                            )
                        ],
                        tags=None,
                    ),
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="passed_test",
                                entries=[],
                            )
                        ],
                        tags=None,
                    ),
                    TestGroupReport(
                        name="Error Handler",
                        category=ReportCategories.SYNTHESIZED,
                        entries=[
                            TestCaseReport(
                                name="error_handler_fn",
                                entries=[
                                    {
                                        "description": "Error handler ran!",
                                        "type": "Log",
                                    }
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    check_report(expected_report, mockplan.report)


def test_failure_with_no_error_handler(mockplan):
    multitest = MultiTest(
        name="MyMultitest",
        suites=[FailingSuite()],
        error_handler=error_handler_fn,
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MyMultitest",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="FailingSuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="failed_test",
                                entries=[
                                    {
                                        "description": "Failed test",
                                        "passed": False,
                                        "type": "Fail",
                                    }
                                ],
                            )
                        ],
                        tags=None,
                    ),
                ],
            )
        ],
    )

    check_report(expected_report, mockplan.report)
