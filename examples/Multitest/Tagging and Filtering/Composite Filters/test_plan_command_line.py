#!/usr/bin/env python
"""
This example shows how test filters can be composed via command line arguments.
"""
import sys

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.multitest import MultiTest, testcase, testsuite


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
    @testcase(tags="server")
    def test_1(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_2(self, env, result):
        pass

    @testcase(tags={"simple": "server", "color": "blue"})
    def test_3(self, env, result):
        pass


@testsuite(tags=("server", "client"))
class Gamma:
    @testcase(tags={"color": "red"})
    def test_1(self, env, result):
        pass

    @testcase(tags={"color": ("blue", "green")})
    def test_2(self, env, result):
        pass

    @testcase(tags={"color": "yellow"})
    def test_3(self, env, result):
        pass


@testsuite
class Delta:
    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass


# Composite filtering via command line arguments currently support
# tag and pattern based filtering with some limitations:

# OR composition between different filtering categories (e.g. Tag & Pattern)
# is not supported on command line filtering.
# This means when `--tags` and `--patterns` are used together, only
# the tests that match BOTH filters will be run.

# AND composition between same filtering categories
# (e.g. Tag + Tag, Pattern + Pattern) is not supported on
# command line filtering.

# This means when `--tags server` and `--tags client` are used together,
# tests that match ANY of these rules will be run.

# `Not` meta filter is not supported via command line options, you need
# to rely on programmatic filtering to make use of this feature.


# You can run the current Testplan script with the sample command line
# arguments below to see how command line filtering works:


# Run tests tagged with `color = red` OR `color = yellow`
# OR tagged with `server` AND `color = blue`
# command line: `--tags color=red,yellow --tags-all server color=blue`


# Run tests that have the name `test_2` and are tagged with `color = blue`
# command line: `--patterns *:*:test_2 --tags color=blue`


# Run all tests: tagged with `server`
# AND (belong to `Gamma` multitest OR has the name `test_3`)
# command line: `--tags server --patterns Gamma *:*:test_3`
# command line (alt.): `--tags server --patterns Gamma --patterns *:*:test_3`


@test_plan(
    name="Composite Filters (Command line)",
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style("testcase", "testcase"),
)
def main(plan):

    multi_test_1 = MultiTest(name="Primary", suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name="Secondary", suites=[Gamma()])
    multi_test_3 = MultiTest(name="Other", suites=[Delta()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)
    plan.add(multi_test_3)


if __name__ == "__main__":
    sys.exit(not main())
