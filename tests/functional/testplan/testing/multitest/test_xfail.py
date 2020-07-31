from testplan.testing.multitest import MultiTest, testsuite, testcase, xfail


@testsuite
class StrictXfailedSuite(object):
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
class NoStrictXfailedSuite(object):
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be fail", strict=False)
    def test_fail(self, env, result, val):
        result.true(val > 100, description="Check if value is true")

    @testcase(parameters=tuple(range(10)))
    @xfail("Should be pass", strict=False)
    def test_pass(self, env, result, val):
        result.true(val < 100, description="Check if value is true")


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
