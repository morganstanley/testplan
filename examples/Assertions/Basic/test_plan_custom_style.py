#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to customize the style of assertion header on web UI.
"""

import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SimpleSuite(object):
    @testcase
    def test_styled_assertions(self, env, result):
        # Basic assertion containing argument `custom_style`
        result.equal(
            "foo",
            "foo",
            description="Equality test",
            custom_style={"color": "#4A2BFF", "background-color": "#FFDDDD"},
        )
        result.log(
            "This is a example of applying custom style",
            description="Log a message",
            custom_style={"font-size": "200%", "font-style": "italic"},
        )

        # `group` method does not accept argument `custom_style`, while the
        # assertion methods in the group can accept argument `custom_style`.
        with result.group(description="Custom group description") as group:
            group.greater(
                5,
                3,
                description="Greater than",
                custom_style={"background-color": "#FFFFC4"},
            )
            group.less(
                6,
                4,
                description="Less than",
                custom_style={"background-color": "#FFFFC4"},
            )


@test_plan(
    name="Custom Styles of Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Custom Styles of Assertions Test",
            suites=[
                SimpleSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
