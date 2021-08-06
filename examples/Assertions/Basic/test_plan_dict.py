#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of dict assertion namespaces.
"""
import re
import sys
from testplan import test_plan
from testplan.common.utils import comparison
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class DictSuite:
    """
    `result.dict` namespace can be used for applying advanced
    assertion rules to dictionaries, which can be nested.
    """

    @testcase
    def test_dict_namespace(self, env, result):

        actual = {"foo": 1, "bar": 2}

        expected = {"foo": 1, "bar": 5, "extra-key": 10}

        # `dict.match` (recursively) matches elements of the dictionaries
        result.dict.match(actual, expected, description="Simple dict match")

        # `dict.match` supports nested data as well

        actual = {"foo": {"alpha": [1, 2, 3], "beta": {"color": "red"}}}

        expected = {"foo": {"alpha": [1, 2], "beta": {"color": "blue"}}}

        result.dict.match(actual, expected, description="Nested dict match")

        # It is possible to use custom comparators with `dict.match`
        actual = {
            "foo": [1, 2, 3],
            "bar": {"color": "blue"},
            "baz": "hello world",
        }

        expected = {
            "foo": [1, 2, lambda v: isinstance(v, int)],
            "bar": {"color": comparison.In(["blue", "red", "yellow"])},
            "baz": re.compile(r"\w+ world"),
        }

        result.dict.match(
            actual, expected, description="Dict match: Custom comparators"
        )

        # You can also specify a comparator function to apply to all values in
        # your dict. Standard comparators are available under
        # testplan.common.utils.comparison.COMPARE_FUNCTIONS but any function
        # f(x: Any, y: Any) -> bool can be used.
        actual = {"foo": 1, "bar": 2, "baz": 3}
        expected = {"foo": 1.0, "bar": 2.0, "baz": 3.0}

        result.dict.match(
            actual,
            expected,
            description="default assertion passes because the values are "
            "numerically equal",
        )
        result.dict.match(
            actual,
            expected,
            description="when we check types the assertion will fail",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["check_types"],
        )

        actual = {"foo": 1.02, "bar": 2.28, "baz": 3.50}
        expected = {"foo": 0.98, "bar": 2.33, "baz": 3.46}
        result.dict.match(
            actual,
            expected,
            description="use a custom comparison function to check within a "
            "tolerance",
            value_cmp_func=lambda x, y: abs(x - y) < 0.1,
        )

        # The report_mode can be specified to limit the comparison
        # information stored. By default all comparisons are stored and added
        # to the report, but you can choose to discard some comparisons to
        # reduce the size of the report when comparing very large dicts.
        actual = {"key{}".format(i): i for i in range(10)}
        expected = actual.copy()
        expected["bad_key"] = "expected"
        actual["bad_key"] = "actual"
        result.dict.match(
            actual,
            expected,
            description="only report the failing comparison",
            report_mode=comparison.ReportOptions.FAILS_ONLY,
        )

        # `dict.check` can be used for checking existence / absence
        # of keys within a dictionary

        result.dict.check(
            dictionary={"foo": 1, "bar": 2, "baz": 3},
            has_keys=["foo", "alpha"],
            absent_keys=["bar", "beta"],
        )

        # `dict.log` can be used to log a dictionary in human readable format.

        result.dict.log(
            dictionary={
                "foo": [1, 2, 3],
                "bar": {"color": "blue"},
                "baz": "hello world",
            }
        )


@test_plan(
    name="Dict Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Dict Assertions Test",
            suites=[
                DictSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
