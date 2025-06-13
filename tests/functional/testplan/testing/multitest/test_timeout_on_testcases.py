import time

from testplan.testing.multitest import MultiTest, testsuite, testcase, timeout

from testplan.runners.pools.base import Pool as ThreadPool
from testplan.runners.pools.tasks import Task

from testplan.common.utils.testing import check_report
from testplan.report import (
    Status,
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
)


@testsuite
class Suite1:
    """A test suite with basic testcases."""

    @testcase(timeout=3)
    def test_normal(self, env, result):
        result.log("Testcase will finish execution in time")

    @testcase(timeout=2)
    def test_abnormal(self, env, result):
        result.log("Testcase will definitely timeout")
        time.sleep(5)


@testsuite
class Suite2:
    """A test suite with parameterized testcases in different exec groups."""

    @testcase(parameters=(1, 2, 0.5), execution_group="first", timeout=5)
    def test_not_timeout(self, env, result, val):
        result.log("Testcase will sleep for {} seconds".format(val))
        time.sleep(val)

    @testcase(parameters=(1, 0.5, 5), execution_group="second", timeout=2)
    def test_timeout(self, env, result, val):
        result.log("Testcase will sleep for {} seconds".format(val))
        time.sleep(val)


@testsuite
class Suite3(object):
    """A test suite with teardown method and it will timeout."""

    @timeout(3)
    def setup(self, env, result):
        result.log("Setup method will sleep for 1 second")
        time.sleep(1)

    @testcase
    def test_normal(self, env, result):
        result.log("Testcase will finish execution in time")

    @timeout(1)
    def teardown(self, env):
        time.sleep(3)


@testsuite
class Suite4(object):
    """A test suite with setup method and it will timeout."""

    @timeout(1)
    def setup(self, env, result):
        result.log("Setup method will sleep for 5 seconds")
        time.sleep(5)

    @testcase
    def test_abnormal(self, env, result):
        result.log("Testcase will never run")

    def teardown(self, env, result):
        result.log("Teardown method can still run")


@testsuite
class Suite5(object):
    """A test suite with pre/post testcase methods which may not run."""

    @timeout(3)
    def pre_testcase(self, name, env, result):
        result.log("Pre testcase method will always be OK")
        time.sleep(1)

    @timeout(2)
    def post_testcase(self, name, env, result, kwargs):
        val = kwargs.get("val")
        if val < 2:
            result.log("Post testcase method can still run")
        time.sleep(val)

    @testcase(parameters=(1, 5))
    def test_method(self, env, result, val):
        result.log(f"Get value {val}")
        result.log("Testcase will finish in a short time")


def get_mtest1():
    return MultiTest(
        name="MTest1", suites=[Suite1(), Suite2()], thread_pool_size=2
    )


def get_mtest2():
    return MultiTest(
        name="MTest2",
        suites=[Suite3(), Suite4()],
        stop_on_error=True,
    )


def get_mtest3():
    return MultiTest(name="MTest3", suites=[Suite5()], stop_on_error=True)


def _create_testcase_report(name, status_override=None, entries=None):
    report = TestCaseReport(name=name)
    report.status_override = status_override
    if entries:
        report.entries = entries
    return report


def test_timeout_on_testcases(mockplan):
    pool = ThreadPool(name="MyPool", size=2)
    mockplan.add_resource(pool)

    task = Task(target=get_mtest1())
    mockplan.schedule(task, resource="MyPool")

    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MTest1",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="Suite1",
                        description="A test suite with basic testcases.",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="test_normal",
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Testcase will finish execution in time",
                                    }
                                ],
                            ),
                            _create_testcase_report(
                                name="test_abnormal",
                                status_override=Status.ERROR,
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Testcase will definitely timeout",
                                    }
                                ],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite2",
                        description="A test suite with parameterized testcases in different exec groups.",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestGroupReport(
                                name="test_not_timeout",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_not_timeout <val=1>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 1 seconds",
                                            }
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_not_timeout <val=2>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 2 seconds",
                                            }
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_not_timeout <val=0.5>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 0.5 seconds",
                                            }
                                        ],
                                    ),
                                ],
                            ),
                            TestGroupReport(
                                name="test_timeout",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_timeout <val=1>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 1 seconds",
                                            }
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_timeout <val=0.5>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 0.5 seconds",
                                            }
                                        ],
                                    ),
                                    _create_testcase_report(
                                        name="test_timeout <val=5>",
                                        status_override=Status.ERROR,
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Testcase will sleep for 5 seconds",
                                            }
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    check_report(expected_report, mockplan.report)


def test_timeout_on_suite_related_methods(mockplan):
    pool = ThreadPool(name="MyPool", size=1)
    mockplan.add_resource(pool)

    task = Task(target=get_mtest2())
    mockplan.schedule(task, resource="MyPool")

    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MTest2",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="Suite3",
                        description="A test suite with teardown method and it will timeout.",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestCaseReport(
                                name="setup",
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Setup method will sleep for 1 second",
                                    }
                                ],
                            ),
                            TestCaseReport(
                                name="test_normal",
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Testcase will finish execution in time",
                                    }
                                ],
                            ),
                            _create_testcase_report(
                                name="teardown",
                                status_override=Status.ERROR,
                                entries=[],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="Suite4",
                        description="A test suite with setup method and it will timeout.",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            _create_testcase_report(
                                name="setup",
                                status_override=Status.ERROR,
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Setup method will sleep for 5 seconds",
                                    }
                                ],
                            ),
                            TestCaseReport(
                                name="teardown",
                                entries=[
                                    {
                                        "type": "Log",
                                        "message": "Teardown method can still run",
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


def test_timeout_on_case_related_methods(mockplan):
    pool = ThreadPool(name="MyPool", size=1)
    mockplan.add_resource(pool)

    task = Task(target=get_mtest3())
    mockplan.schedule(task, resource="MyPool")

    mockplan.run()

    expected_report = TestReport(
        name="plan",
        entries=[
            TestGroupReport(
                name="MTest3",
                category=ReportCategories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name="Suite5",
                        description="A test suite with pre/post testcase methods which may not run.",
                        category=ReportCategories.TESTSUITE,
                        entries=[
                            TestGroupReport(
                                name="test_method",
                                category=ReportCategories.PARAMETRIZATION,
                                entries=[
                                    TestCaseReport(
                                        name="test_method <val=1>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Pre testcase method will always be OK",
                                            },
                                            {
                                                "type": "Log",
                                                "message": "Get value 1",
                                            },
                                            {
                                                "type": "Log",
                                                "message": "Testcase will finish in a short time",
                                            },
                                            {
                                                "type": "Log",
                                                "message": "Post testcase method can still run",
                                            },
                                        ],
                                    ),
                                    TestCaseReport(
                                        name="test_method <val=5>",
                                        entries=[
                                            {
                                                "type": "Log",
                                                "message": "Pre testcase method will always be OK",
                                            },
                                            {
                                                "type": "Log",
                                                "message": "Get value 5",
                                            },
                                            {
                                                "type": "Log",
                                                "message": "Testcase will finish in a short time",
                                            },
                                        ],
                                        status_override=Status.ERROR,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    check_report(expected_report, mockplan.report)
    assert (
        "`post_testcase` timeout"
        in mockplan.report["MTest3"]["Suite5"]["test_method"][
            "test_method__val_5"
        ].logs[0]["message"]
    )
