from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.common.utils.testing import (
    check_report,
    log_propagation_disabled,
)
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class MySuite(object):
    @testcase
    def test_one(self, env, result):
        pass


def check_func_1(env, result):
    result.equal(1, 1, description="sample assertion")


def check_func_2(env):
    pass


def check_func_3(env):
    pass


def check_func_4(env, result):
    result.equal(1, 2, description="failing assertion")


expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyMultitest",
            category=ReportCategories.MULTITEST,
            entries=[
                TestGroupReport(
                    name="MySuite",
                    category=ReportCategories.TESTSUITE,
                    entries=[TestCaseReport(name="test_one")],
                ),
                TestGroupReport(
                    name="Pre/Post Step Checks",
                    category=ReportCategories.TESTSUITE,
                    entries=[
                        TestCaseReport(
                            name="before_start - check_func_1",
                            entries=[{"type": "Equal", "passed": True}],
                        ),
                        TestCaseReport(name="after_start - check_func_2"),
                        TestCaseReport(name="before_stop - check_func_3"),
                        TestCaseReport(
                            name="after_stop - check_func_4",
                            entries=[{"type": "Equal", "passed": False}],
                        ),
                    ],
                ),
            ],
        )
    ],
)


def test_pre_post_steps():

    multitest = MultiTest(
        name="MyMultitest",
        suites=[MySuite()],
        before_start=check_func_1,
        after_start=check_func_2,
        before_stop=check_func_3,
        after_stop=check_func_4,
    )

    plan = TestplanMock(name="plan", parse_cmdline=False)
    plan.add(multitest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan.run()

    check_report(expected_report, plan.report)
