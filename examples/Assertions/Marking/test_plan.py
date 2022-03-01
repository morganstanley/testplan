#!/usr/bin/env python
"""
This example demonstrates the usage of the mark decorator.
"""
from testplan import test_plan
from testplan.testing.multitest import testcase, testsuite, MultiTest
from testplan.testing.multitest.result import mark


def helper(result):
    result.fail(description="Failure in helper.")


@mark
def helper_marked(result):
    result.fail(description="Failure in marked helper.")


@mark
def intermediary(result):
    helper(result)


@mark
def intermediary_marked(result):
    helper_marked(result)


@testsuite(name="Example suite")
class Suite:
    @testcase(name="Testcase")
    def test_unmarked(self, env, result):
        """
        Upon failure, points to assertion in helper.
        """
        helper(result)

    @testcase(name="Testcase with marked helper")
    def test_marked_helper(self, env, result):
        """
        Upon failure, points to assertion in helper_marked.
        """
        helper_marked(result)

    @testcase(name="Testcase with marked intermediary")
    def test_marked_intermediary(self, env, result):
        """
        Upon failure, points to call of helper in intermediary.
        """
        intermediary(result)

    @testcase(name="Testcase with marked intermediary and helper")
    def test_marked_intermediary_helper(self, env, result):
        """
        Upon failure, points to assertion in helper_marked.
        """
        intermediary_marked(result)


@test_plan(name="Plan")
def main(plan):
    plan.add(MultiTest(name="MultiTest", suites=[Suite()]))
    return plan


if __name__ == "__main__":
    main()
