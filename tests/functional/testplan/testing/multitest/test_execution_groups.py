import time
from collections import OrderedDict

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.common.utils.testing import log_propagation_disabled
from testplan.report import TestGroupReport
from testplan.common.utils.logger import TESTPLAN_LOGGER

EXECUTION_PERIOD = 0.001


@testsuite
class MySuite(object):
    @testcase
    def test_case_0_0(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_1")
    def test_case_1_0(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_2")
    def test_case_2_0(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase
    def test_case_0_1(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_1")
    def test_case_1_1(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_2")
    def test_case_2_1(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase
    def test_case_0_2(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_1")
    def test_case_1_2(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(execution_group="group_2")
    def test_case_2_2(self, env, result):
        time.sleep(EXECUTION_PERIOD)

    @testcase(
        parameters=(("x", 1), ("y", 2), ("z", 3)), execution_group="group_3"
    )
    def test_case_3(self, env, result, a, b):
        time.sleep(EXECUTION_PERIOD)


def get_testcase_execution_time(
    report, suite_name="MySuite", multitest_name="MyMultitest"
):
    for multitest_report in report.entries:
        testcase_execution_time = OrderedDict()

        if multitest_report.name != multitest_name:
            continue

        for suite_report in multitest_report.entries:
            if suite_report.name != suite_name:
                continue

            for entry in suite_report.entries:
                if isinstance(entry, TestGroupReport):
                    testcase_execution_time.update(
                        {
                            testcase_report.name: testcase_report.timer["run"]
                            for testcase_report in entry
                        }
                    )
                else:
                    testcase_execution_time[entry.name] = entry.timer["run"]

        return testcase_execution_time


def test_execution_order():

    multitest = MultiTest(
        name="MyMultitest", suites=[MySuite()], thread_pool_size=2
    )

    plan = TestplanMock(name="plan", parse_cmdline=False)
    plan.add(multitest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan.run()

    result = get_testcase_execution_time(plan.report)

    group_1_start = min(
        result[item].start for item in result if item.startswith("test_case_1")
    )
    group_2_start = min(
        result[item].start for item in result if item.startswith("test_case_2")
    )
    group_3_start = min(
        result[item].start for item in result if item.startswith("test_case_3")
    )
    group_0_end = max(
        result[item].end for item in result if item.startswith("test_case_0")
    )
    group_1_end = max(
        result[item].end for item in result if item.startswith("test_case_1")
    )
    group_2_end = max(
        result[item].end for item in result if item.startswith("test_case_2")
    )

    assert (
        result["test_case_0_0"].start
        < result["test_case_0_0"].end
        <= result["test_case_0_1"].start
        < result["test_case_0_1"].end
        <= result["test_case_0_2"].start
        < result["test_case_0_2"].end
    )
    assert group_0_end <= group_1_start
    assert group_1_end <= group_2_start
    assert group_2_end <= group_3_start
