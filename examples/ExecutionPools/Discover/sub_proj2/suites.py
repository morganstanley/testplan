"""This file contains testsuite definition"""

from testplan.testing.multitest import testsuite, testcase


@testsuite
class Suite1:
    """A test suite with several normal testcases."""

    @testcase
    def test_equal(self, env, result):
        result.equal("foo", "foo", description="Equality example")

    @testcase
    def test_not_equal(self, env, result):
        result.not_equal("foo", "bar", description="Inequality example")

    @testcase
    def test_less(self, env, result):
        result.less(2, 12, description="Less comparison example")

    @testcase
    def test_greater(self, env, result):
        result.greater(10, 5, description="Greater comparison example")

    @testcase
    def test_approximate_equal(self, env, result):
        result.isclose(
            100,
            101,
            rel_tol=0.01,
            abs_tol=0.0,
            description="Approximate equality example",
        )


@testsuite
class Suite2:
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(6)))
    def test_bool(self, env, result, val):
        if val > 0:
            result.true(val, description="Check if value is true")
        else:
            result.false(val, description="Check if value is false")
