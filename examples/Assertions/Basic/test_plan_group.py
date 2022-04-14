#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of assertion group.
"""
import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class GroupSuite:
    """
    result object has a `group` method that can be used for grouping
    assertions together. This has no effect on stdout, however it will
    be formatted with extra indentation on PDF reports for example.
    """

    @testcase
    def test_assertion_group(self, env, result):

        result.equal(1, 1, description="Equality assertion outside the group")

        with result.group(description="Custom group description") as group:
            group.not_equal(2, 3, description="Assertion within a group")
            group.greater(5, 3)

            # Groups can have sub groups as well:
            with group.group(description="This is a sub group") as sub_group:
                sub_group.less(6, 3, description="Assertion within sub group")

        result.equal(
            "foo", "foo", description="Final assertion outside all groups"
        )


@test_plan(
    name="Group Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Group Assertions Test",
            suites=[
                GroupSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
