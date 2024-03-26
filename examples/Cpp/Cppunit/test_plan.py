#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to use Cppunit test runner.

To be able to run the test, you need to compile the files
under `test` directory first to a binary target named `runTests`
"""

import os
import sys

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.cpp import Cppunit

BINARY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test", "runTests"
)


def before_start(env, result):
    result.log("Executing before start hook.")


def after_start(env, result):
    result.log("Executing after start hook.")


def before_stop(env, result):
    result.log("Executing before stop hook.")


def after_stop(env, result):
    result.log("Executing after stop hook.")


@test_plan(
    name="Cppunit Example",
    stdout_style=Style(passing="testcase", failing="assertion-detail"),
)
def main(plan):

    if not os.path.exists(BINARY_PATH):
        raise RuntimeError("You need to compile test binary first.")

    else:
        plan.add(
            Cppunit(
                name="My Cppunit",
                binary=BINARY_PATH,
                file_output_flag="-y",
                before_start=before_start,
                after_start=after_start,
                before_stop=before_stop,
                after_stop=after_stop,
            )
        )
        # You can apply Cppunit specific filtering via `filtering_flag` arg
        # and `cppunit_filter` arg, for example:
        # Cppunit(... filtering_flag='-t', cppunit_filter='LogicalOp::TestOr')
        # And you can also implement listing feature via `listing_flag` arg,
        # for example:
        # Cppunit(... listing_flag='-l')
        # But please be sure that your Cppunit binary is able to recognize
        # those '-y', '-t' and '-l' flags.


if __name__ == "__main__":
    sys.exit(not main())
