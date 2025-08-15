import pathlib
import pytest
from testplan import TestplanMock
from testplan.testing import multitest
from testplan.exporters.testing.failed_tests import (
    FailedTestsExporter,
    FailedTestLevel,
)


@multitest.testsuite
class Alpha:
    def setup(self, env, result):
        result.log("within suite setup...")

    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "passing assertion")

    @multitest.testcase(parameters=(1, 2, 3))
    def test_param(self, env, result, arg):
        result.equal(arg, 2, f"failing assertion with arg {arg}")

    @multitest.testcase
    def test_fail(self, env, result):
        result.equal(1, 2, "failing assertion")


@multitest.testsuite
class Beta:
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.not_equal(5, 5)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


@multitest.testsuite
class Gamma:
    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "passing assertion")


def failed_after_start(env, result):
    """
    This function is called after the test suite starts.
    It can be used to perform any necessary setup or checks.
    """
    result.fail("This is a failed after start function.")


@pytest.mark.parametrize(
    "level, failed_tests",
    (
        (FailedTestLevel.MULTITEST, ["alpha", "beta", "gamma"]),
        (FailedTestLevel.TESTSUITE, ["alpha:Alpha", "beta:Beta", "gamma"]),
        (
            FailedTestLevel.TESTCASE,
            [
                "alpha:Alpha:test_param <arg=1>",
                "alpha:Alpha:test_param <arg=3>",
                "alpha:Alpha:test_fail",
                "beta:Beta:test_failure",
                "beta:Beta:test_error",
                "gamma",
            ],
        ),
    ),
)
def test_failed_tests_exporter(runpath, level, failed_tests):
    failed_tests_path = pathlib.Path(runpath) / "failed_tests.txt"
    plan = TestplanMock(
        "plan",
        exporters=FailedTestsExporter(
            dump_failed_tests=str(failed_tests_path), failed_tests_level=level
        ),
        runpath=runpath,
    )
    multitest_1 = multitest.MultiTest(name="alpha", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="beta", suites=[Beta()])
    multitest_3 = multitest.MultiTest(
        name="gamma", suites=[Gamma()], after_start=failed_after_start
    )
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.add(multitest_3)
    plan.run()
    assert failed_tests_path.exists()
    assert failed_tests_path.stat().st_size > 0, "Failed tests file is empty"
    with failed_tests_path.open("r") as f:
        content = f.read()
    assert "\n".join(failed_tests) == content.strip()
