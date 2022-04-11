#!/usr/bin/env python
"""
This example shows how different sorting logic can be applied
on different testing levels (e.g. plan, multitest)
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.ordering import ShuffleSorter, AlphanumericSorter


@testsuite
class Alpha:
    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


@testsuite
class Beta:
    @testcase
    def test_c(self, env, result):
        pass

    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


@testsuite
class Zeta:
    @testcase
    def test_c(self, env, result):
        pass

    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


@testsuite
class Gamma:
    @testcase
    def test_c(self, env, result):
        pass

    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


# We have a plan level test sorter that will sort the tests alphabetically
# However on Multitest('Primary') we have an explicit `test_sorter` argument
# which will take precedence and shuffle the tests instead.
@test_plan(
    name="Multi-level Test ordering",
    test_sorter=AlphanumericSorter("all"),
    # Using testcase level stdout so we can see sorted testcases
    stdout_style=Style("testcase", "testcase"),
)
def main(plan):

    multi_test_1 = MultiTest(
        name="Primary",
        test_sorter=ShuffleSorter("all"),
        suites=[Alpha(), Beta()],
    )

    multi_test_2 = MultiTest(name="Secondary", suites=[Zeta(), Gamma()])

    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
