# ``stop_on_error`` deprecated, for testing compatibility

import time

import testplan.testing.multitest as mt
from testplan.common.utils.testing import check_report
from testplan.report import (
    ReportCategories,
    Status,
    TestCaseReport,
    TestGroupReport,
    TestReport,
)


@mt.testsuite
class Suite1:
    def setup(self, env, result):
        pass

    @mt.testcase
    def test_case_1(self, env, result):
        pass

    @mt.testcase
    def test_case_2(self, env, result):
        raise Exception("Exception raised for no reason")

    @mt.testcase
    def test_case_3(self, env, result):
        pass

    def teardown(self, env, result):
        pass


@mt.testsuite
class Suite2:
    def setup(self, env, result):
        pass

    @mt.testcase(parameters=(-1, 0, 1))
    def test_case_divide_by_arg(self, env, result, arg):
        result.equal(1, arg / arg, "{} / {} == 1".format(arg, arg))

    @mt.testcase(parameters=(-1, 0, 1))
    def test_case_divide_by_one(self, env, result, arg):
        result.equal(arg, arg / 1, "{} / 1 == {}".format(arg, arg))

    def teardown(self, env, result):
        pass


@mt.testsuite
class Suite3:
    def setup(self, env, result):
        pass

    @mt.testcase(execution_group="first")
    def test_case_first_group_1(self, env, result):
        pass

    @mt.testcase(execution_group="second")
    def test_case_second_group_1(self, env, result):
        pass

    @mt.testcase(execution_group="first")
    def test_case_first_group_2(self, env, result):
        time.sleep(5)  # enough time for executing testcases in 'first' group
        raise Exception("Exception raised for no reason")

    @mt.testcase(execution_group="second")
    def test_case_second_group_2(self, env, result):
        pass

    @mt.testcase(execution_group="first")
    def test_case_first_group_3(self, env, result):
        pass

    @mt.testcase(execution_group="second")
    def test_case_second_group_3(self, env, result):
        pass

    def teardown(self, env, result):
        pass


def _create_testcase_report(name, status_override=None):
    report = TestCaseReport(name=name)
    report.status_override = status_override
    return report


def test_execution_order(mockplan):
    multitest_1 = mt.MultiTest(
        name="Multitest_1",
        suites=[Suite1(), Suite2(), Suite3()],
        thread_pool_size=2,
        stop_on_error=False,
    )
    multitest_2 = mt.MultiTest(
        name="Multitest_2",
        suites=[Suite1(), Suite2(), Suite3()],
        thread_pool_size=2,
        stop_on_error=True,
    )

    mockplan.add(multitest_1)
    mockplan.add(multitest_2)
    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="Multitest_1",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="Suite1",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestCaseReport(name="test_case_1"),
                            _create_testcase_report(
                                name="test_case_2",
                                status_override=Status.ERROR,
                            ),
                            TestCaseReport(name="test_case_3"),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite2",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestGroupReport(
                                name="test_case_divide_by_arg",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_case_divide_by_arg <arg=-1>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": 1,
                                                "second": 1,
                                            }
                                        ],
                                    ),
                                    _create_testcase_report(
                                        name="test_case_divide_by_arg <arg=0>",
                                        status_override=Status.ERROR,
                                    ),
                                    TestCaseReport(
                                        name="test_case_divide_by_arg <arg=1>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": 1,
                                                "second": 1,
                                            }
                                        ],
                                    ),
                                ],
                            ),
                            TestGroupReport(
                                name="test_case_divide_by_one",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_case_divide_by_one <arg=-1>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": -1,
                                                "second": -1,
                                            }
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_case_divide_by_one <arg=0>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": 0,
                                                "second": 0,
                                            }
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_case_divide_by_one <arg=1>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": 1,
                                                "second": 1,
                                            }
                                        ],
                                    ),
                                ],
                            ),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite3",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestCaseReport(name="test_case_first_group_1"),
                            _create_testcase_report(
                                name="test_case_first_group_2",
                                status_override=Status.ERROR,
                            ),
                            TestCaseReport(name="test_case_first_group_3"),
                            TestCaseReport(name="test_case_second_group_1"),
                            TestCaseReport(name="test_case_second_group_2"),
                            TestCaseReport(name="test_case_second_group_3"),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                ],
            ),
            TestGroupReport(
                name="Multitest_2",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="Suite1",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestCaseReport(name="test_case_1"),
                            _create_testcase_report(
                                name="test_case_2",
                                status_override=Status.ERROR,
                            ),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite2",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestGroupReport(
                                name="test_case_divide_by_arg",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_case_divide_by_arg <arg=-1>",
                                        entries=[
                                            {
                                                "type": "Equal",
                                                "first": 1,
                                                "second": 1,
                                            }
                                        ],
                                    ),
                                    _create_testcase_report(
                                        name="test_case_divide_by_arg <arg=0>",
                                        status_override=Status.ERROR,
                                    ),
                                ],
                            ),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite3",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(name="setup"),
                            TestCaseReport(name="test_case_first_group_1"),
                            _create_testcase_report(
                                name="test_case_first_group_2",
                                status_override=Status.ERROR,
                            ),
                            TestCaseReport(name="test_case_first_group_3"),
                            TestCaseReport(name="teardown"),
                        ],
                    ),
                ],
            ),
        ],
    )

    check_report(expected_report, mockplan.report)
