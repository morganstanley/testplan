import pytest
from schema import SchemaError

from testplan import TestplanMock
from testplan.common.report.base import Status
from testplan.testing.multitest import MultiTest, testcase, testsuite, xfail

from .test_multitest_drivers import BaseDriver, VulnerableDriver1


@testsuite
class StrictXfailedSuite:
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be fail", strict=True)
    def test_fail(self, env, result, val):
        result.true(val > 100, description="Check if value is true")

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be pass", strict=True)
    def test_pass(self, env, result, val):
        result.true(val < 100, description="Check if value is true")


@testsuite
class NoStrictXfailedSuite:
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be fail", strict=False)
    def test_fail(self, env, result, val):
        result.true(val > 100, description="Check if value is true")

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be pass", strict=False)
    def test_pass(self, env, result, val):
        result.true(val < 100, description="Check if value is true")


@testsuite
class DynamicXfailSuite:
    """A test suite to check dynamic allocation of xfail decorator"""

    name = "DynamicXfailSuiteAlias"

    @testcase
    def test_1(self, env, result):
        result.equal(2, 3)

    @testcase(parameters=(3,))
    def test_2(self, env, result, n):
        result.equal(2, n)


@testsuite
class SetupFailSuite:
    def setup(self, env, result):
        result.equal(2, 3)

    @testcase
    def dummy_case(self, env, result):
        result.log("dummy case")

    def teardown(self, env, result):
        raise RuntimeError("raise in testsuite teardown on purpose")


@testsuite
class AssertionXfailSuite:
    @testcase
    def runtime_error_case(self, env, result):
        raise RuntimeError("raise in testcase on purpose")

    @testcase
    def dict_match_case(self, env, result):
        result.dict.match(
            {"foo": 1},
            {"foo": 2},
            description="custom dict match description",
        )


def error_hook(env, result):
    raise RuntimeError("hook raise on purpose")


class LogEmittingStartupFailureDriver(BaseDriver):
    def __init__(self, *args, marker, **kwargs):
        self._marker = marker
        super().__init__(*args, **kwargs)

    def starting(self):
        super().starting()
        self.std.out.write(f"{self._marker}\n")
        self.std.out.flush()
        self.std.err.write(f"{self._marker}\n")
        self.std.err.flush()
        raise Exception("Startup error")


def test_dynamic_xfail():
    plan = TestplanMock(
        name="dynamic_xfail_test",
        xfail_tests={
            "Dummy:DynamicXfailSuiteAlias:test_1": {
                "reason": "known flaky",
                "strict": False,
            },
            "Dummy:DynamicXfailSuiteAlias:test_2 <n=3>": {
                "reason": "unknown non-flaky",
                "strict": True,
            },
            "Startup Error:*:*": {
                "reason": "known flaky",
                "strict": False,
            },
            "Testsuite Setup Error:Environment Start:After Start": {
                "reason": "known flaky",
                "strict": False,
            },
            "Testsuite Setup Error:SetupFailSuite:setup": {
                "reason": "known flaky",
                "strict": False,
            },
            "Testsuite Setup Error:SetupFailSuite:teardown": {
                "reason": "known flaky",
                "strict": False,
            },
        },
    )
    plan.add(MultiTest(name="Dummy", suites=[DynamicXfailSuite()]))
    plan.add(
        MultiTest(
            name="Startup Error",
            suites=SetupFailSuite(),  # this is not executed anyway
            environment=[
                VulnerableDriver1(
                    name="vulnerable_driver_1", report_errors_from_logs=True
                )
            ],
        )
    )
    plan.add(
        MultiTest(
            name="Testsuite Setup Error",
            suites=SetupFailSuite(),
            after_start=error_hook,
        )
    )

    result = plan.run()

    dynamic_xfail_suite_report = result.report.entries[0].entries[0]
    assert dynamic_xfail_suite_report.unstable is True
    assert dynamic_xfail_suite_report.entries[0].unstable is True

    assert result.report.entries[1].unstable is True
    # after start
    assert result.report.entries[2].entries[0].entries[0].unstable is True
    # setup
    assert result.report.entries[2].entries[1].entries[0].unstable is True
    # teardown
    assert result.report.entries[2].entries[1].entries[2].unstable is True


def test_dynamic_xfail_environment_start_when_logs():
    plan = TestplanMock(
        name="dynamic_xfail_environment_start_when_logs",
        xfail_tests={
            "First Startup Error:Environment Start:Starting": {
                "reason": "known startup failure with matching logs",
                "strict": False,
                "when": {"logs": "hahaha"},
            },
            "Second Startup Error:Environment Start:Starting": {
                "reason": "known startup failure with non-matching logs",
                "strict": False,
                "when": {"logs": "hahaha"},
            },
        },
    )
    plan.add(
        MultiTest(
            name="First Startup Error",
            suites=SetupFailSuite(),
            environment=[
                LogEmittingStartupFailureDriver(
                    name="failing_driver_1",
                    marker="hahaha",
                    report_errors_from_logs=True,
                )
            ],
        )
    )
    plan.add(
        MultiTest(
            name="Second Startup Error",
            suites=SetupFailSuite(),
            environment=[
                LogEmittingStartupFailureDriver(
                    name="failing_driver_2",
                    marker="hohoho",
                    report_errors_from_logs=True,
                )
            ],
        )
    )

    result = plan.run()

    first_env_start = result.report["First Startup Error"][
        "Environment Start"
    ]["Starting"]
    second_env_start = result.report["Second Startup Error"][
        "Environment Start"
    ]["Starting"]

    assert first_env_start.unstable is True
    assert first_env_start.status == Status.XFAIL
    assert second_env_start.failed is True
    assert second_env_start.status == Status.ERROR


def test_dynamic_xfail_testcase_when_assertions():
    plan = TestplanMock(
        name="dynamic_xfail_testcase_when_assertions",
        xfail_tests={
            "Assertion Xfail MT:AssertionXfailSuite:runtime_error_case": {
                "reason": "runtime error should not match assertion filter",
                "strict": False,
                "when": {
                    "assertions": {
                        "type": "DictMatch",
                        "description": "custom dict match description",
                    }
                },
            },
            "Assertion Xfail MT:AssertionXfailSuite:dict_match_case": {
                "reason": "dict match failure should match assertion filter",
                "strict": False,
                "when": {
                    "assertions": {
                        "type": "DictMatch",
                        "description": "custom dict match description",
                    }
                },
            },
        },
    )
    plan.add(
        MultiTest(
            name="Assertion Xfail MT",
            suites=[AssertionXfailSuite()],
        )
    )

    result = plan.run()

    suite_report = result.report["Assertion Xfail MT"]["AssertionXfailSuite"]
    runtime_error_case = suite_report["runtime_error_case"]
    dict_match_case = suite_report["dict_match_case"]

    assert runtime_error_case.status == Status.ERROR
    assert dict_match_case.status == Status.XFAIL


def test_dynamic_xfail_bad_when_schema():
    with pytest.raises(SchemaError, match="Key 'xfail_tests' error"):
        _ = TestplanMock(
            name="dynamic_xfail_bad_when_schema",
            xfail_tests={
                "Assertion Xfail MT:AssertionXfailSuite:dict_match_case": {
                    "reason": "invalid assertions matcher should fail plan",
                    "strict": False,
                    "when": {
                        "assertions": {
                            "passed": False,
                        }
                    },
                },
            },
        )


def test_xfail(mockplan):
    mockplan.add(
        MultiTest(
            name="xfail_test",
            suites=[StrictXfailedSuite(), NoStrictXfailedSuite()],
        )
    )
    result = mockplan.run()

    assert result.report.failed

    strict_xfail_suite_report = result.report.entries[0].entries[0]
    assert strict_xfail_suite_report.counter == {
        "passed": 0,
        "failed": 0,
        "total": 20,
        "xfail": 10,
        "xpass-strict": 10,
    }
    assert strict_xfail_suite_report.failed is True
    assert strict_xfail_suite_report.entries[0].unstable is True
    assert strict_xfail_suite_report.entries[1].failed is True

    no_strict_xfail_suite_report = result.report.entries[0].entries[1]
    assert no_strict_xfail_suite_report.counter == {
        "passed": 0,
        "failed": 0,
        "total": 20,
        "xfail": 10,
        "xpass": 10,
    }
    assert no_strict_xfail_suite_report.unstable is True
    assert no_strict_xfail_suite_report.entries[0].unstable is True
    assert no_strict_xfail_suite_report.entries[1].unstable is True
