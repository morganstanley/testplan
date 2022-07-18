#!/usr/bin/env python
"""
This example shows usage of skip assertion.
"""
import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SkipSuite:
    @testcase
    def skip_me(self, env, result):
        result.true(True)
        result.skip("call skip assertion")
        result.fail("skip me")

    @testcase(parameters=tuple(range(10)))
    def condition_skip(self, env, result, num):
        if num % 2 == 0:
            result.skip("This testcase is marked as skipped")
        else:
            result.log("This is a log message")


@test_plan(
    name="Skip Assertion Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Skip Assertion Test",
            suites=[
                SkipSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
