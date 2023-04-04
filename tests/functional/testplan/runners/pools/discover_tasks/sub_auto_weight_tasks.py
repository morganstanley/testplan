from testplan.runners.pools.tasks.base import task_target
from testplan.testing.multitest import MultiTest, testsuite, testcase


@testsuite
class Suite1:
    """A test suite with several normal testcases."""

    @testcase
    def test1(self, env, result):
        result.equal("foo", "foo", description="Equality example")

    @testcase
    def test2(self, env, result):
        result.not_equal("foo", "bar", description="Inequality example")

    @testcase
    def test3(self, env, result):
        result.less(2, 12, description="Less comparison example")

    @testcase
    def test4(self, env, result):
        result.greater(10, 5, description="Greater comparison example")


@testsuite
class Suite2:
    """A test suite with parameterized testcases."""

    @testcase(parameters=tuple(range(6)))
    def test_bool(self, env, result, val):
        if val > 0:
            result.true(val, description="Check if value is true")
        else:
            result.false(val, description="Check if value is false")


@task_target(multitest_parts=2)
def make_auto_weight_multitest1():
    return MultiTest(name="Proj1-suite", suites=[Suite1(), Suite2()])
