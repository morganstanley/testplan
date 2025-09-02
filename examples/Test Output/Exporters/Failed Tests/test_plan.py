#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
Demonstrates how to generate a Failed Tests report using --patterns-file.
"""

import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan


@testsuite
class AlphaSuite:
    @testcase
    def test_equality_passing(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def test_equality_failing(self, env, result):
        result.equal(2, 1, description="failing equality")

    @testcase
    def test_membership_passing(self, env, result):
        result.contain(1, [1, 2, 3], description="passing membership")

    @testcase
    def test_membership_failing(self, env, result):
        result.contain(
            member=1,
            container={"foo": 1, "bar": 2},
            description="failing membership",
        )

    @testcase
    def test_regex_passing(self, env, result):
        result.regex.match(
            regexp="foo", value="foobar", description="passing regex match"
        )

    @testcase
    def test_regex_failing(self, env, result):
        result.regex.match(
            regexp="bar", value="foobaz", description="failing regex match"
        )


@testsuite
class BetaSuite:
    @testcase
    def passing_testcase_one(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def passing_testcase_two(self, env, result):
        result.equal("foo", "foo", description="another passing equality")


# The `@test_plan` decorator supports the `dump_failed_tests` argument
# to generate Failed Tests reports without explicitly using a FailedTestsExporter.

# Alternatively, you can generate a Failed Tests report via the command line:
# ./test_plan.py --dump-failed-tests <report-path>

# Ensure <report-path> is a valid file path.

# For testing command line configuration, use the `--dump-failed-tests` argument,
# as it overrides programmatic declarations.


@test_plan(
    name="Basic Failed Tests Report Example",
    dump_failed_tests=os.path.join(
        os.path.dirname(__file__), "failed_tests.txt"
    ),
)
def main(plan):
    multi_test_1 = MultiTest(name="Primary", suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name="Secondary", suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(main().exit_code)
