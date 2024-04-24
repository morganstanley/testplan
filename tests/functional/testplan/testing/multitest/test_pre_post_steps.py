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
                        name="Environment Start",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="check_func_1",
                                uid="check_func_1",
                                entries=[{"type": "Equal", "passed": True}],
                            ),
                            TestCaseReport(
                                name="starting", uid="starting", entries=[]
                            ),
                            TestCaseReport(
                                name="check_func_2",
                                uid="check_func_2",
                                entries=[],
                            ),
                        ],
                        tags=None,
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
                        name="Environment Stop",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="check_func_3",
                                uid="check_func_3",
                                entries=[],
                            ),
                            TestCaseReport(
                                name="stopping", uid="stopping", entries=[]
                            ),
                            TestCaseReport(
                                name="check_func_4",
                                uid="check_func_4",
                                entries=[
                                    {"type": "Equal", "passed": False},
                                    {"type": "Attachment"},
                                ],
                            ),
                        ],
                        tags=None,
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
                        name="Environment Start",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="starting", uid="starting", entries=[]
                            ),
                            TestCaseReport(
                                name="check_func_2",
                                uid="check_func_2",
                                entries=[],
                            ),
                        ],
                        tags=None,
                    ),
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="test_one"),
                            TestCaseReport(
                                name="teardown",
                                category=ReportCategories.SYNTHESIZED,
                                entries=[{"type": "Attachment"}],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="Environment Stop",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="stopping", uid="stopping", entries=[]
                            )
                        ],
                        tags=None,
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
                        name="Environment Start",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="starting", uid="starting", entries=[]
                            )
                        ],
                        tags=None,
                    ),
                    TestGroupReport(
                        name="MySuite",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="test_one"),
                            TestCaseReport(
                                name="teardown",
                                category=ReportCategories.SYNTHESIZED,
                                entries=[{"type": "Attachment"}],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="Environment Stop",
                        category="synthesized",
                        entries=[
                            TestCaseReport(
                                name="stopping", uid="stopping", entries=[]
                            )
                        ],
                        tags=None,
                    ),
                ],
            ),
        ],
    )

    check_report(expected_report, mockplan.report)
