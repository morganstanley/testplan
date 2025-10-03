#!/usr/bin/env python
"""
Example demonstrating the --testcase-timeout CLI option.

This script can be run with:
    python test_cli_timeout_example.py
    python test_cli_timeout_example.py --testcase-timeout 2

When run with --testcase-timeout 2, the slow_test will timeout and fail.
"""
import time
import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase


@testsuite
class MySuite:
    """Example test suite with tests of varying duration."""

    @testcase
    def fast_test(self, env, result):
        """This test completes quickly."""
        result.log("Fast test completing")
        result.true(True, description="Fast assertion")

    @testcase
    def slow_test(self, env, result):
        """This test takes 5 seconds."""
        result.log("Slow test starting - will take 5 seconds")
        time.sleep(5)
        result.log("Slow test completed")
        result.true(True, description="Slow assertion")

    @testcase(timeout=10)
    def test_with_explicit_timeout(self, env, result):
        """This test has explicit 10s timeout."""
        result.log("Test with explicit timeout")
        time.sleep(1)
        result.true(True, description="Explicit timeout assertion")


@test_plan(name="TestcaseTimeoutExample")
def main(plan):
    """
    Add a MultiTest to the plan. The testcase timeout can be controlled
    via the --testcase-timeout CLI argument.
    """
    plan.add(
        MultiTest(
            name="MyTest",
            suites=[MySuite()],
        )
    )


if __name__ == "__main__":
    # Run with: python test_cli_timeout_example.py --testcase-timeout 2
    sys.exit(not main())
