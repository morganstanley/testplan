#!/usr/bin/env python
"""
This example shows how to use HobbesTest test runner.
The example uses a mocked test binary, and you can replace it with a link to your actual test binary.
"""

import os
import sys

from testplan import test_plan
from testplan.testing.cpp import HobbesTest

BINARY_PATH = os.path.join(os.path.dirname(__file__), "test", "hobbes-test")


def before_start(env, result):
    result.log("Executing before start hook.")


def after_start(env, result):
    result.log("Executing after start hook.")


def before_stop(env, result):
    result.log("Executing before stop hook.")


def after_stop(env, result):
    result.log("Executing after stop hook.")


@test_plan(name="HobbesTest Example")
def main(plan):
    if not os.path.exists(BINARY_PATH):
        raise RuntimeError("You need to compile test binary first.")

    else:
        plan.add(
            HobbesTest(
                name="My HobbesTest",
                binary=BINARY_PATH,
                before_start=before_start,
                after_start=after_start,
                before_stop=before_stop,
                after_stop=after_stop,
                # You can run one or more specified test(s)
                # tests=['Arrays', 'Compiler', 'Hog'],
                # You can pass other arguments to the test binary
                # other_args=['--tests', 'Arrays', 'Compiler']
            )
        )


if __name__ == "__main__":
    sys.exit(not main())
