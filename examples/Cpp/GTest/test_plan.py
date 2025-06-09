#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to use GTest test runner.

To be able to run the test, you need to compile the files
under `test` directory first to a binary target named `runTests`
"""

import os
import sys

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.cpp import GTest

BINARY_PATH = os.path.join(os.path.dirname(__file__), "test", "runTests")


def before_start(env, result):
    result.log("Executing before start hook.")


def after_start(env, result):
    result.log("Executing after start hook.")


def before_stop(env, result):
    result.log("Executing before stop hook.")


def after_stop(env, result):
    result.log("Executing after stop hook.")


@test_plan(
    name="GTest Example",
    stdout_style=Style(passing="testcase", failing="assertion-detail"),
)
def main(plan):
    if not os.path.exists(BINARY_PATH):
        raise RuntimeError("You need to compile test binary first.")

    else:
        plan.add(
            GTest(
                name="My GTest",
                binary=BINARY_PATH,
                # You can apply GTest specific filtering via `gtest_filter` arg
                # gtest_filter='SquareRootTest.*',
                # You can also shuffle test order via `gtest_shuffle` arg
                # gtest_shuffle=True
                before_start=before_start,
                after_start=after_start,
                before_stop=before_stop,
                after_stop=after_stop,
            )
        )


if __name__ == "__main__":
    sys.exit(not main())
