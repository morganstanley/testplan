#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of fix assertion namespaces.
"""

import re
import sys
from testplan import test_plan
from testplan.common.utils import comparison
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class FixSuite:
    """
    `result.fix` namespace can be used for applying advanced
    assertion rules to fix messages, which can
    be nested (e.g. repeating groups)
    For more info about FIX protocol, please see:
    https://en.wikipedia.org/wiki/Financial_Information_eXchange
    """

    @testcase
    def test_fix_namespace(self, env, result):
        # `fix.match` can compare two fix messages, and
        # supports custom comparators (like `dict.match`)

        fix_msg_1 = {
            36: 6,
            22: 5,
            55: 2,
            38: 5,
            555: [
                {
                    600: "A",
                    601: "A",
                    683: [{688: "a", 689: None}, {688: "b", 689: "b"}],
                },
                {
                    600: "B",
                    601: "B",
                    683: [{688: "c", 689: "c"}, {688: "d", 689: "d"}],
                },
            ],
        }

        fix_msg_2 = {
            36: 6,
            22: 5,
            55: 2,
            38: comparison.GreaterEqual(4),
            555: [
                {
                    600: "A",
                    601: "B",
                    683: [
                        {688: "a", 689: re.compile(r"[a-z]")},
                        {688: "b", 689: "b"},
                    ],
                },
                {
                    600: "C",
                    601: "B",
                    683: [
                        {688: "c", 689: comparison.In(("c", "d"))},
                        {688: "d", 689: "d"},
                    ],
                },
            ],
        }
        result.fix.match(fix_msg_1, fix_msg_2)

        # `fix.check` can be used for checking existence / absence
        # of certain tags in a fix message

        result.fix.check(
            msg=fix_msg_1, has_tags=[26, 22, 11], absent_tags=[444, 555]
        )

        # `fix.log` can be used to log a fix message in human readable format.

        result.fix.log(
            msg={
                36: 6,
                22: 5,
                55: 2,
                38: 5,
                555: [{556: "USD", 624: 1}, {556: "EUR", 624: 2}],
            }
        )


@test_plan(
    name="Fix Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Fix Assertions Test",
            suites=[
                FixSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
