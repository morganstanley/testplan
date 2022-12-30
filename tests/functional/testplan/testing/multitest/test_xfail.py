from testplan import TestplanMock
from testplan.testing.multitest import MultiTest, testcase, testsuite, xfail


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

    @testcase
    def test_1(self, env, result):
        result.equal(2, 3)

    @testcase(parameters=(3,))
    def test_2(self, env, result, n):
        result.equal(2, n)


def test_dynamic_xfail():
    plan = TestplanMock(
        name="dynamic_xfail_test",
        xfail_tests={
            "Dummy:DynamicXfailSuite:test_1": {
                "reason": "known flaky",
                "strict": False,
            },
            "Dummy:DynamicXfailSuite:test_2 <n=3>": {
                "reason": "unknown non-flaky",
                "strict": True,
            },
        },
    )
    plan.add(MultiTest(name="Dummy", suites=[DynamicXfailSuite()]))
    result = plan.run()

    dynamic_xfail_suite_report = result.report.entries[0].entries[0]

    assert dynamic_xfail_suite_report.unstable is True
    assert dynamic_xfail_suite_report.entries[0].unstable is True


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
