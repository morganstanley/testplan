"""Test for default testcase timeout feature (--testcase-timeout CLI option)."""

import time

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.testing import check_report
from testplan.report import (
    Status,
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
)


@testsuite
class SuiteWithoutTimeout:
    """Testsuite with testcases that don't have explicit timeout."""

    @testcase
    def test_passes_quickly(self, env, result):
        """This test should pass."""
        result.log("Test completes quickly")

    @testcase
    def test_takes_time(self, env, result):
        """This test takes 3 seconds but should timeout with default of 2s."""
        result.log("Test will sleep for 3 seconds")
        time.sleep(3)


@testsuite
class SuiteWithExplicitTimeout:
    """Testsuite with testcases that have explicit timeout."""

    @testcase(timeout=5)
    def test_with_explicit_timeout(self, env, result):
        """This test has explicit timeout that should override default."""
        result.log("Test will sleep for 1 second with 5s timeout")
        time.sleep(1)


def test_default_testcase_timeout_from_config(mockplan):
    """Test that default testcase timeout from config works."""
    # Create MultiTest with explicit testcase_timeout
    multitest = MultiTest(
        name="TestDefaultTimeout",
        suites=[SuiteWithoutTimeout()],
        testcase_timeout=2,  # 2 seconds default timeout
    )
    mockplan.add(multitest)
    mockplan.run()

    # First test should pass (completes quickly)
    assert mockplan.report.status == Status.ERROR
    test_report = mockplan.report["TestDefaultTimeout"]["SuiteWithoutTimeout"]
    assert test_report["test_passes_quickly"].status == Status.PASSED
    # Second test should timeout and have ERROR status
    assert test_report["test_takes_time"].status == Status.ERROR


def test_explicit_timeout_overrides_default(mockplan):
    """Test that explicit testcase timeout overrides the default."""
    multitest = MultiTest(
        name="TestExplicitOverride",
        suites=[SuiteWithExplicitTimeout()],
        testcase_timeout=1,  # 1 second default, but test has 5s explicit
    )
    mockplan.add(multitest)
    mockplan.run()

    # Test should pass because explicit timeout (5s) overrides default (1s)
    assert mockplan.report.status == Status.PASSED
    test_report = mockplan.report["TestExplicitOverride"]["SuiteWithExplicitTimeout"]
    assert test_report["test_with_explicit_timeout"].status == Status.PASSED


def test_no_default_timeout(mockplan):
    """Test that testcases work normally without default timeout."""
    multitest = MultiTest(
        name="TestNoDefault",
        suites=[SuiteWithoutTimeout()],
        # No testcase_timeout specified
    )
    mockplan.add(multitest)
    mockplan.run()

    # Both tests should pass without any timeout
    assert mockplan.report.status == Status.PASSED
    test_report = mockplan.report["TestNoDefault"]["SuiteWithoutTimeout"]
    assert test_report["test_passes_quickly"].status == Status.PASSED
    assert test_report["test_takes_time"].status == Status.PASSED


def test_testcase_timeout_inheritance_from_parent(mockplan):
    """Test that testcase_timeout is inherited from parent config."""
    # Set testcase_timeout in parent (mockplan) config
    mockplan.cfg.set_local("testcase_timeout", 2)
    
    # Create MultiTest without explicit testcase_timeout
    multitest = MultiTest(
        name="TestInheritance",
        suites=[SuiteWithoutTimeout()],
    )
    mockplan.add(multitest)
    mockplan.run()

    # First test should pass, second should timeout
    assert mockplan.report.status == Status.ERROR
    test_report = mockplan.report["TestInheritance"]["SuiteWithoutTimeout"]
    assert test_report["test_passes_quickly"].status == Status.PASSED
    assert test_report["test_takes_time"].status == Status.ERROR
