#!/usr/bin/env python
"""
This example shows how to use HobbesTest test runner.
The example uses a mocked test binary, and you can replace it with a link to your actual test binary.
"""

import os
import sys

from testplan.testing.cpp import HobbesTest

from testplan import test_plan

BINARY_PATH = os.path.join(os.path.dirname(__file__), "test", "hobbes-test")


@test_plan(name="HobbesTest Example")
def main(plan):

    if not os.path.exists(BINARY_PATH):
        raise RuntimeError("You need to compile test binary first.")

    else:
        plan.add(
            HobbesTest(
                name="MyHobbesTest",
                binary=BINARY_PATH,
                # You can run one or more specified test(s)
                # tests=['Arrays', 'Compiler', 'Hog'],
                # You can pass other arguments to the test binary
                # other_args=['--tests', 'Arrays', 'Compiler']
            )
        )


if __name__ == "__main__":
    sys.exit(not main())
