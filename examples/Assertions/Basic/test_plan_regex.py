#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of regex assertion namespaces.
"""
import re
import os
import sys
from testplan import test_plan
from testplan.common.utils import comparison
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class RegexSuite:
    """
    `result.regex` contains methods for regular expression assertions
    """

    @testcase
    def test_regex_namespace(self, env, result):

        # `regex.match` applies `re.match` with the given `regexp` and `value`
        result.regex.match(
            regexp="foo", value="foobar", description="string pattern match"
        )

        # We can also pass compiled SRE objects as well:
        result.regex.match(
            regexp=re.compile("foo"), value="foobar", description="SRE match"
        )

        # `regex.multiline_match` implicitly passes `re.MULTILINE`
        # and `re.DOTALL` flags to `re.match`

        multiline_text = os.linesep.join(
            ["first line", "second line", "third line"]
        )

        result.regex.multiline_match("first line.*second", multiline_text)

        # `regex.not_match` returns True if the
        # given pattern does not match the value

        result.regex.not_match("baz", "foobar")

        # `regex.multiline_not_match` implicitly passes `re.MULTILINE`
        # and `re.DOTALL` flags to `re.match`

        result.regex.multiline_not_match("foobar", multiline_text)

        # `regex.search` runs pattern match via `re.search`
        result.regex.search("second", multiline_text)

        # `regex.search_empty` returns True when the given
        # pattern does not exist in the text.
        result.regex.search_empty(
            "foobar", multiline_text, description="Passing search empty"
        )

        result.regex.search_empty(
            "second", multiline_text, description="Failing search_empty"
        )

        # `regex.findall` matches all of the occurrences of the pattern
        # in the given string and optionally runs an extra condition function
        # against the number of matches
        text = "foo foo foo bar bar foo bar"

        result.regex.findall(
            regexp="foo",
            value=text,
            condition=lambda num_matches: 2 < num_matches < 5,
        )

        # Equivalent assertion with more readable output
        result.regex.findall(
            regexp="foo",
            value=text,
            condition=comparison.Greater(2) & comparison.Less(5),
        )

        # `regex.matchline` can be used for checking if a given pattern
        # matches one or more lines in the given text
        result.regex.matchline(
            regexp=re.compile(r"\w+ line$"), value=multiline_text
        )


@test_plan(
    name="Regex Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Regex Assertions Test",
            suites=[
                RegexSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
