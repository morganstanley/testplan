#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""This example shows how to generate XML reports in JUnit format."""
import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan import test_plan


@testsuite
class AlphaSuite:
    @testcase
    def test_equality_passing(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def test_equality_failing(self, env, result):
        result.equal(2, 1, description="failing equality")

    @testcase
    def test_membership_passing(self, env, result):
        result.contain(1, [1, 2, 3], description="passing membership")


@testsuite
class BetaSuite:
    @testcase
    def test_error(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def passing_testcase_two(self, env, result):
        result.equal("foo", "foo", description="another passing equality")


# `@test_plan` accepts shortcut argument `xml_dir` for XML output, meaning
# you don't have to instantiate an XMLExporter explicitly for basic XML
# report generation.

# XML reports can also be generated via command line arguments like:
# ./test_plan.py --xml <xml-directory>

# <xml-directory> should be a valid system directory, if this directory already
# exists it will be removed and recreated.

# If you want to test out command line configuration for XML generation
# please directly use --xml argument because command line arguments can
# override programmatic declaration.


@test_plan(
    name="Basic XML Report Example",
    xml_dir=os.path.join(os.path.dirname(__file__), "xml"),
)
def main(plan):
    multi_test_1 = MultiTest(name="Primary", suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name="Secondary", suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
