#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of checking exception.
"""

import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class RaisedSuite:
    """
    result` object has `raises` and `not_raises` methods that can be
    as context managers to check if a given block of code raises / not
    raises a given exception
    """

    @testcase
    def test_raised_exceptions(self, env, result):
        with result.raises(KeyError):
            {"foo": 3}["bar"]

        # Exception message pattern check (`re.search` is used implicitly)

        with result.raises(
            ValueError,
            pattern="foobar",
            description="Exception raised with custom pattern.",
        ):
            raise ValueError("abc foobar xyz")

        # Custom function check (func should accept
        # exception object as a single arg)

        class MyException(Exception):
            def __init__(self, value):
                self.value = value

        def custom_func(exc):
            return exc.value % 2 == 0

        with result.raises(
            MyException,
            func=custom_func,
            description="Exception raised with custom func.",
        ):
            raise MyException(4)

        # `not_raises` passes when raised exception
        # type does match any of the declared exception classes
        # It is logically inverse of `result.raises`.

        with result.not_raises(TypeError):
            {"foo": 3}["bar"]

        # `not_raises` can also check if a certain exception has been raised
        # WITHOUT matching the given `pattern` or `func`

        # Exception type matches but pattern does not -> Pass
        with result.not_raises(
            ValueError,
            pattern="foobar",
            description="Exception not raised with custom pattern.",
        ):
            raise ValueError("abc")

        # Exception type matches but func does not -> Pass
        with result.not_raises(
            MyException,
            func=custom_func,
            description="Exception not raised with custom func.",
        ):
            raise MyException(5)


@test_plan(
    name="Exception Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Exception Assertions Test",
            suites=[
                RaisedSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
