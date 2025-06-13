#!/usr/bin/env python
"""
This example shows how the run order for your suites / testcases
can be configured via command line options.
"""

import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


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


# You can try running the current script with the sample arguments below
# to see how the tests can be shuffled / sorted via command line arguments.

# Just shuffle the testcases, keep original ordering of suites.
# command line: `--shuffle testcases`

# Shuffle the suites only, using seed value of 15
# command line: `--shuffle suites --shuffle-seed 15`

# Shuffle suites and testcases (suites, testcases)
# command line: `--shuffle suites testcases`


@test_plan(
    name="Test Ordering / Shuffling basics (Command line)",
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
