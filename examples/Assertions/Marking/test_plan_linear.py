#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example demonstrates the usage of the mark decorator for linear cases.
"""
import sys

from testplan import test_plan
from testplan.testing.multitest import testcase, testsuite, MultiTest
from testplan.testing.result import report_target


def helper(result):
    result.fail(description="Failure in helper.")


def intermediary(result):
    helper(result)


@report_target
def intermediary_marked(result):
    helper(result)


@testsuite(name="Example suite for linear testcases")
class Suite:
    @testcase(name="Testcase with no marking.")
    def test_unmarked(self, env, result):
        """
        Upon failure, points to assertion in helper.
        """
        helper(result)

    @testcase(name="Testcase with marked intermediary")
    def test_intermediary(self, env, result):
        """
        Upon failure, points to assertion in helper.
        """
        intermediary(result)

    @testcase(name="Testcase with marked intermediary and helper")
    def test_marked_intermediary(self, env, result):
        """
        Upon failure, points to call of helper in intermediary_marked.
        """
        intermediary_marked(result)


@test_plan(name="Plan")
def main(plan):
    plan.add(
        MultiTest(
            name="MultiTest", suites=[Suite()], testcase_report_target=False
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
