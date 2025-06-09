#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example demonstrates the usage of the mark decorator for non-linear cases.
"""

import sys

from testplan import test_plan
from testplan.testing.multitest import testcase, testsuite, MultiTest
from testplan.testing.result import report_target


def helper(result):
    result.fail(description="Failure in helper.")


@report_target
def helper_marked(result):
    result.fail(description="Failure in marked helper.")


def intermediary(result):
    helper(result)


@report_target
def intermediary_marked(result, both):
    helper(result)
    if both:
        helper_marked(result)


@testsuite(name="Example suite")
class Suite:
    @testcase(name="Testcase with marked helper")
    def test_non_linear(self, env, result):
        """
        Non-linear test case for demonstrating various scenarios.
        """
        # Points to assertion in testcase.
        result.fail(description="Failure in testcase.")
        # Points to assertion in unmarked utility function.
        helper(result)
        # Points to assertion in umarked utility function, not intermediary.
        intermediary(result)
        # Points to marked intermediary instead of unmarked utility function.
        intermediary_marked(result, both=False)
        # Points to marked utility function instead of marked intermediary.
        intermediary_marked(result, both=True)


@test_plan(name="Plan")
def main(plan):
    plan.add(
        MultiTest(
            name="MultiTest", suites=[Suite()], testcase_report_target=False
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
