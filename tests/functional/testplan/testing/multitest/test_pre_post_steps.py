import os
from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan.common.utils.testing import check_report
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    Status,
)

CURRENT_FILE = os.path.abspath(__file__)


@testsuite
class MySuite:
    @testcase
    def test_one(self, env, result):
        pass

    def teardown(self, env, result):
        result.attach(os.__file__, description="attache file in teardown")


def check_func_1(env, result):
    result.equal(1, 1, description="sample assertion")


def check_func_2(env):
    pass


def check_func_3(env):
    pass


def check_func_4(env, result):
    result.equal(1, 2, description="failing assertion")
    result.attach(CURRENT_FILE, description="current file")


def test_pre_post_steps(mockplan):

    multitest = MultiTest(
        name="MyMultitest",
        suites=[MySuite()],
        before_start=check_func_1,
        after_start=check_func_2,
        before_stop=check_func_3,
        after_stop=check_func_4,
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
                        name="Before Start",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="check_func_1",
                                entries=[{"type": "Equal", "passed": True}],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="After Start",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="check_func_2",
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="test_one"),
                            TestCaseReport(
                                name="teardown",
                                entries=[{"type": "Attachment"}],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="Before Stop",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="check_func_3"),
                        ],
                    ),
                    TestGroupReport(
                        name="After Stop",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="check_func_4",
                                entries=[
                                    {"type": "Equal", "passed": False},
                                    {"type": "Attachment"},
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    check_report(expected_report, mockplan.report)
    assert len(mockplan.report.attachments) == 2


def test_empty_pre_post_steps(mockplan):
    """
    Runs a MultiTest without an empty after_start, expects it present and passing.
    """
    multitest = MultiTest(
        name="MyMultiTest",
        suites=[MySuite()],
        after_start=check_func_2,
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MyMultiTest",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="After Start",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="check_func_2"),
                        ],
                    ),
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="test_one"),
                            TestCaseReport(
                                name="teardown",
                                entries=[{"type": "Attachment"}],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    assert mockplan.report["MyMultiTest"].status == Status.PASSED
    assert mockplan.report.status == Status.PASSED
    check_report(expected_report, mockplan.report)


def test_no_pre_post_steps(mockplan):
    """
    Runs a MultiTest w/o pre/post steps, expects no pre/post step report.
    """
    multitest = MultiTest(
        name="MyMultiTest",
        suites=[MySuite()],
    )
    mockplan.add(multitest)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MyMultiTest",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="test_one"),
                            TestCaseReport(
                                name="teardown",
                                entries=[{"type": "Attachment"}],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    check_report(expected_report, mockplan.report)
