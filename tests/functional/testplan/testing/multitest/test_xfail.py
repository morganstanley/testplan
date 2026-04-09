import json
import os
import re
import subprocess
import sys
import tempfile
from itertools import count

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
    @xfail(
        "Should be fail",
        strict=True,
        condition={
            "failed": {"type": "IsTrue", "description": "Check if value"}
        },
    )
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


def test_dynamic_xfail_environment_start_condition_error():
    plan = TestplanMock(
        name="dynamic_xfail_environment_start_condition_error",
        xfail_tests={
            "First Startup Error:Environment Start:Starting": {
                "reason": "known startup failure with matching error",
                "strict": False,
                "condition": {"error": "hahaha"},
            },
            "Second Startup Error:Environment Start:Starting": {
                "reason": "known startup failure with non-matching error",
                "strict": False,
                "condition": {"error": "hahaha"},
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


@testsuite
class AssertionXfailSuite:
    @testcase
    def only_a1_fails(self, env, result):
        """a1 fails, b1 passes; xfail condition=b1 should not match."""
        result.dict.match(
            {"foo": 1},
            {"foo": 2},
            description="a1 dict match",
        )
        result.dict.match(
            {"bar": 1},
            {"bar": 1},
            description="b1 dict match",
        )

    @testcase
    def neither_fails(self, env, result):
        """a1 and b1 both pass; xfail condition=b1 should not match."""
        result.dict.match(
            {"foo": 1},
            {"foo": 1},
            description="a1 dict match",
        )
        result.dict.match(
            {"bar": 1},
            {"bar": 1},
            description="b1 dict match",
        )

    @testcase
    def both_fail_condition_b1(self, env, result):
        """Both a1 and b1 fail."""
        result.dict.match(
            {"foo": 1},
            {"foo": 2},
            description="a1 dict match",
        )
        result.dict.match(
            {"bar": 1},
            {"bar": 2},
            description="b1 dict match",
        )

    @testcase
    def both_fail_condition_a1(self, env, result):
        """Both a1 and b1 fail."""
        result.dict.match(
            {"foo": 1},
            {"foo": 2},
            description="a1 dict match",
        )
        result.dict.match(
            {"bar": 1},
            {"bar": 2},
            description="b1 dict match",
        )


def test_dynamic_xfail_testcase_condition_failed():
    plan = TestplanMock(
        name="dynamic_xfail_testcase_condition_failed",
        xfail_tests={
            "Assertion Xfail MT:AssertionXfailSuite:only_a1_fails": {
                "reason": "b1 not present so condition should not match",
                "strict": True,
                "condition": {
                    "failed": {
                        "type": "DictMatch",
                        "description": "b1 dict match",
                    }
                },
            },
            "Assertion Xfail MT:AssertionXfailSuite:neither_fails": {
                "reason": "neither failed, condition partially match",
                "strict": True,
                "condition": {
                    "failed": {
                        "type": "DictMatch",
                        "description": "b1 dict match",
                    }
                },
            },
            "Assertion Xfail MT:AssertionXfailSuite:both_fail_condition_b1": {
                "reason": "b1 present and failed so condition should match",
                "strict": False,
                "condition": {
                    "failed": {
                        "type": "DictMatch",
                        "description": "b1 dict match",
                    }
                },
            },
            "Assertion Xfail MT:AssertionXfailSuite:both_fail_condition_a1": {
                "reason": "a1 present and failed so condition should match",
                "strict": True,
                "condition": {
                    "failed": {
                        "type": "DictMatch",
                        "description": "a1 dict match",
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
    only_a1 = suite_report["only_a1_fails"]
    neither = suite_report["neither_fails"]
    both_b1 = suite_report["both_fail_condition_b1"]
    both_a1 = suite_report["both_fail_condition_a1"]

    # only_a1_fails: a1 fails but xfail condition=b1 desc -> no b1 -> not xfail
    assert only_a1.status == Status.FAILED
    # neither_fails: a1 and b1 both pass, xfail condition=b1 desc -> match but not failed -> not xfail
    assert neither.status == Status.XPASS_STRICT
    # both_fail_condition_b1: a1+b1 fail, xfail condition=b1 desc -> match -> xfail
    assert both_b1.status == Status.XFAIL
    # both_fail_condition_a1: a1+b1 fail, xfail condition=a1 desc -> match -> xfail
    assert both_a1.status == Status.XFAIL


@pytest.mark.parametrize(
    "bad_condition",
    [
        {"failed": {"passed": False}},
        {"failed": {"type": "DictMatch"}, "error": "some pattern"},
    ],
    ids=count(0),
)
def test_dynamic_xfail_bad_condition_schema(bad_condition):
    with pytest.raises(SchemaError, match="Key 'xfail_tests' error"):
        _ = TestplanMock(
            name="dynamic_xfail_bad_condition_schema",
            xfail_tests={
                "Assertion Xfail MT:AssertionXfailSuite:both_fail_condition_b1": {
                    "reason": "invalid condition schema should fail plan",
                    "strict": False,
                    "condition": bad_condition,
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


EXAMPLE_PLAN = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "..",
    "examples",
    "App",
    "Basic",
    "test_plan.py",
)


def test_xfail_cli():
    """
    End-to-end test for --xfail-tests CLI argument.

    1. Generates a failing plan script from examples/App/Basic/test_plan.py
       by replacing ``testplan`` with ``testplannn`` inside re.compile().
    2. First run: produces a JSON report from the failing plan.
    3. Extracts xfail entries from the report, including a ``condition.error``
       pattern from the first error entry containing "While starting".
    4. Second run: feeds the xfail JSON via --xfail-tests and verifies
       the resulting report has xfail status overrides.
    """
    content = open(EXAMPLE_PLAN).read()
    content = re.sub(
        r'(re\.compile\(r")testplan(")',
        r"\1testplannn\2",
        content,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        plan_script = os.path.join(tmpdir, "test_plan.py")
        with open(plan_script, "w") as f:
            f.write(content)

        # --- First run: collect the failure report ---
        first_json = os.path.join(tmpdir, "first_report.json")
        proc1 = subprocess.run(
            [sys.executable, plan_script, "--json", first_json],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert os.path.exists(first_json), (
            f"First run JSON report not produced.\n"
            f"stdout: {proc1.stdout}\nstderr: {proc1.stderr}"
        )

        with open(first_json) as f:
            first_report = json.load(f)

        # Sanity: the plan should have failed
        assert first_report["status"] == "error"

        # --- Extract xfail entries from the first report ---
        xfail_tests = {}
        for mt in first_report["entries"]:
            mt_name = mt["name"]
            for suite in mt["entries"]:
                suite_name = suite["name"]
                for case in suite["entries"]:
                    case_name = case["name"]
                    if case["status"] == "error":
                        pattern = f"{mt_name}:{suite_name}:{case_name}"
                        # we know we only have environment startup error here
                        assert (
                            suite_name == "Environment Start"
                            and case_name == "Starting"
                        )
                        # "condition" from first log containing "While starting"
                        # we already know that so we hardcode it here
                        msg = case["logs"][0].get("message", "")
                        assert "While starting" in msg
                        entry = {
                            "reason": "known failure",
                            "strict": False,
                            "condition": {"error": "While starting"},
                        }
                        xfail_tests[pattern] = entry

        assert xfail_tests, "No xfail patterns extracted from first report"

        # --- Second run: apply xfail and verify ---
        xfail_json_path = os.path.join(tmpdir, "xfail.json")
        with open(xfail_json_path, "w") as f:
            json.dump(xfail_tests, f)

        second_json = os.path.join(tmpdir, "second_report.json")
        proc2 = subprocess.run(
            [
                sys.executable,
                plan_script,
                "--xfail-tests",
                xfail_json_path,
                "--json",
                second_json,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert os.path.exists(second_json), (
            f"Second run JSON report not produced.\n"
            f"stdout: {proc2.stdout}\nstderr: {proc2.stderr}"
        )

        with open(second_json) as f:
            second_report = json.load(f)

        mt = second_report["entries"][0]
        assert mt["name"] == "TestEcho"

        # Find the Starting case under Environment Start
        env_start = next(
            s for s in mt["entries"] if s["name"] == "Environment Start"
        )
        starting = env_start["entries"][0]
        assert starting["name"] == "Starting"
        assert starting["status_override"] == "xfail"
