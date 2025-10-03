#!/usr/bin/env python
"""
Example demonstrating the --testcase-timeout CLI option.

Usage:
------
Run without timeout (all tests pass):
    python cli_timeout_example.py

Run with 2-second default timeout (slow_test will timeout):
    python cli_timeout_example.py --testcase-timeout 2

Run with 10-second default timeout (all tests pass):
    python cli_timeout_example.py --testcase-timeout 10

Description:
------------
This example demonstrates how to use the --testcase-timeout CLI option to set
a default timeout for all testcases in a MultiTest. Testcases that don't
complete within the timeout will be marked as ERROR.

The example contains three tests:
1. fast_test: Completes quickly (< 1 second)
2. slow_test: Takes 5 seconds to complete
3. test_with_explicit_timeout: Has an explicit 10-second timeout set

When run with --testcase-timeout 2:
- fast_test passes (completes in < 2 seconds)
- slow_test times out and fails (takes 5 seconds > 2 second default)
- test_with_explicit_timeout passes (explicit 10s timeout overrides the 2s default)
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
    sys.exit(not main())
