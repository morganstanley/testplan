#!/usr/bin/env python
"""
This example shows how the run order for your tests / suites / testcases
can be configured programmatically.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.ordering import (
    NoopSorter,
    ShuffleSorter,
    AlphanumericSorter,
    SortType,
)


@testsuite
class Alpha(object):
    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


@testsuite
class Beta(object):
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
class Gamma(object):
    @testcase
    def test_c(self, env, result):
        pass

    @testcase
    def test_b(self, env, result):
        pass

    @testcase
    def test_a(self, env, result):
        pass


# This is the sorter that's used by default:
# Test cases are run in their original declaration order.
# Test suites are run in the order they are added to a multitest.
# Multitests (instances) are run in the order they are added to the plan.

noop_sorter = NoopSorter()


# You can shuffle your test runs by using the built-in ShuffleSorter.
# This is advised as a good practice in case you are running testcases in
# parallel and they have race conditions.

# Just shuffle the testcases, keep original ordering of suites.
testcase_shuffler_a = ShuffleSorter("testcases")
testcase_shuffler_b = ShuffleSorter(SortType.TEST_CASES)


# Shuffle the suites only, using seed value of 15
suite_shuffler_a = ShuffleSorter(shuffle_type="suites", seed=15)
suite_shuffler_b = ShuffleSorter(shuffle_type=SortType.SUITES, seed=15)


# Shuffle suites & testcases
suite_testcase_shuffler_a = ShuffleSorter(("suites", "testcases"))
suite_testcase_shuffler_b = ShuffleSorter(
    shuffle_type=(SortType.SUITES, SortType.TEST_CASES)
)


# There is another built-in sorter that sorts the tests alphabetically:
testcase_alphanumeric_sorter_a = AlphanumericSorter("testcases")
suite_alphanumeric_sorter = AlphanumericSorter("suites")
suite_testcase_alphanumeric_sorter = AlphanumericSorter(
    ("suites", "testcases")
)


# Replace the `test_sorter` argument with the
# sorters / shufflers declared above to see how they work.


@test_plan(
    name="Test Ordering / Shuffling basics (Programmatic)",
    test_sorter=noop_sorter,
    # Using testcase level stdout so we can see sorted testcases
    stdout_style=Style("testcase", "testcase"),
)
def main(plan):

    multi_test_1 = MultiTest(name="Primary", suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name="Secondary", suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
