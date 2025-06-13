#!/usr/bin/env python
"""
This example shows how you can apply different test filters on different levels
(e.g. plan, multitest level)
"""

import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.filtering import Pattern


@testsuite
class Alpha:
    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass


@testsuite
class Beta:
    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass

    @testcase
    def test_3(self, env, result):
        pass


@testsuite
class Gamma:
    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass

    @testcase
    def test_3(self, env, result):
        pass


# In the example below, we have plan level test filter that will run
# test cases that have the name `test_3` only.
#
# However on Multitest('Primary') we also have another test filter that
# will run test cases with the name `test_1`. This filter will take precedence
# over the plan level filter.


@test_plan(
    name="Multi-level Filtering",
    test_filter=Pattern("*:*:test_3"),
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style("testcase", "testcase"),
)
def main(plan):
    multi_test_1 = MultiTest(
        name="Primary",
        suites=[Alpha(), Beta()],
        test_filter=Pattern("*:*:test_1"),
    )
    multi_test_2 = MultiTest(name="Secondary", suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
