#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of assertions,
assertion groups and assertion namespaces.
"""
import os
import re
import sys
import random

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plot


@testsuite
class SampleSuite:
    @testcase
    def test_tkerr(self, env, result):
        result.log_html(
            """
<div style="font-size:80px;font-family:Arial;font-weight:bold;">
    <i class="fa fa-check-square" style="color:green;padding-right:5px;"></i>
    Testplan
</div>
        """,
            description="HTML example",
        )

    @testcase
    def test_basic_assertions(self, env, result):
        # Basic assertions contain equality, comparison, membership checks:
        result.equal("foo", "foo")  # The most basic syntax

        # We can pass description to any assertion method
        result.equal(1, 2, "Description for failing equality")

        result.not_equal("foo", "bar")
        result.greater(5, 2)
        result.greater_equal(2, 2)
        result.greater_equal(2, 1)
        result.less(10, 20)
        result.less_equal(10, 10)
        result.less_equal(10, 30)

        # We can access these assertions via shortcuts as well,
        # They will have the same names with the functions
        # in the built-in `operator` module
        result.eq(15, 15)
        result.ne(10, 20)
        result.lt(2, 3)
        result.gt(3, 2)
        result.le(10, 15)
        result.ge(15, 10)
        result.eq(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )
        # We can test if 2 numbers are close to each other within
        # the relative tolerance or a minimum absolute tolerance level
        result.isclose(100, 95, 0.1, 0.0)
        result.isclose(100, 95, 0.01, 0.0)

        # `result` also has a `log` method that can be used
        # for adding extra information on the output
        result.log(
            "This is a log message, it will be displayed"
            " along with other assertion details."
        )

        result.log(
            """
Multi-line log - will use the first non-empty line as its description and truncate after the 80 char.
The second line shall not occur in description.
            """
        )

        # Boolean checks
        result.true("foo" == "foo", description="Boolean Truthiness check")
        result.false(5 < 2, description="Boolean Falseness check")

        result.fail("This is an explicit failure.")

        # Membership checks
        result.contain("foo", "foobar", description="Passing membership")
        result.not_contain(
            member=10,
            container={"a": 1, "b": 2},
            description="Failing membership",
        )

        # Slice comparison (inclusion)
        result.equal_slices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            ["a", "b", 3, 4, "c", "d", 7, 8],
            slices=[slice(2, 4), slice(6, 8)],
            description="Comparison of slices",
        )

        # Slice comparison (exclusion)
        # For the example below, each separate slice comparison fails
        # however the overall assertion still passes as common exclusion
        # indices of two slices are [2, 3], which is the same values `3`, `4`
        # in both iterables.
        result.equal_exclude_slices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            ["a", "b", 3, 4, "c", "d", "e", "f"],
            slices=[slice(0, 2), slice(4, 8)],
            description="Comparison of slices (exclusion)",
        )

        # We can test if 2 blocks of textual content have differences with
        # comparison option --ignore-space-change, --ignore-whitespaces and
        # --ignore-blank-lines, also we can spefify output delta in unified
        # or context mode.
        result.diff("abc\nxyz\n", "abc\nxyz\n\n", ignore_blank_lines=True)
        result.diff(
            "1\r\n1\r\n1\r\nabc\r\nxy z\r\n2\r\n2\r\n2\r\n",
            "1\n1\n1\nabc \nxy\t\tz\n2\n2\n2\n",
            ignore_space_change=True,
            unified=3,
        )

        # `result` has a `markdown` method that can be used for adding markdown
        # text in the report. Set escape=False to allow raw HTML code.
        result.markdown(
            """
<div style="font-size:80px;font-family:Arial;font-weight:bold;">
    <i class="fa fa-check-square" style="color:green;padding-right:5px;"></i>
    Testplan
</div>

Testplan is a [Python](http://python.org) package that can start a local live
environment, setup mocks, connections to services and run tests against these.
It provides:

  * ``MultiTest`` a feature extensive functional testing system with a rich set
    of *assertions* and report rendering logic.
  * Built-in inheritable drivers to create a local live *environment*.
  * Configurable, diverse and expandable test execution mechanism including
    *parallel* execution capability.
  * Test *tagging* for flexible filtering and selective execution as well as
    generation of multiple reports (for each tag combination).
  * Integration with other unit testing frameworks (like GTest).
  * Rich, unified reports (json/PDF/XML) and soon (HTML/UI).
        """,
            description="Markdown example",
            escape=False,
        )

        # This `log_html` method is a shortcut of `markdown` method  which disabled
        # escape.
        result.log_html(
            """
<div style="font-size:80px;font-family:Arial;font-weight:bold;">
    <i class="fa fa-check-square" style="color:green;padding-right:5px;"></i>
    Testplan
</div>
        """,
            description="HTML example",
        )

        # `result` has a `log_code` method that can be used for adding
        # source code in the report.
        result.log_code(
            """
#include<stdio.h>

int main()
{
    return 0
}
        """,
            language="c",
            description="C codelog example",
        )

        result.log_code(
            """
import os
print(os.uname())
        """,
            language="python",
            description="Python codelog example",
        )

        x = range(0, 10)
        y = range(0, 10)
        plot.plot(x, y)

        result.matplot(
            plot, width=2, height=2, description="Simple matplot example"
        )


@test_plan(
    name="Basic Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Basic Assertions Test",
            suites=[
                SampleSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
