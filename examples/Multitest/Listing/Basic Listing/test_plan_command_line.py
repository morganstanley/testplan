#!/usr/bin/env python
"""
    This example shows how the suites / test cases
    of a test plan can be listed via command line arguments.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan import test_plan


@testsuite
class Alpha(object):
    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags="server")
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_c(self, env, result):
        pass


@testsuite(tags="server")
class Beta(object):
    @testcase(tags="client")
    def test_a(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": ("blue", "yellow")})
    def test_c(self, env, result):
        pass


@testsuite(tags="client")
class Gamma(object):
    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags={"color": ("yellow", "red")})
    def test_b(self, env, result):
        pass

    @testcase(parameters=list(range(100)))
    def test_c(self, env, result, val):
        pass


# Test plan accepts command line options for displaying test information.
# You can try running the current script with the sample arguments below
# to see how you can enable test listing via command line.

# Name listing (trims testcases per suite if they exceed a certain number):
# command line: `--info name`
# command line (shortcut): `--list`

# Sample output:

# Primary
# ..Alpha
# ....test_a
# ....test_b
# ...

# Name listing (without any testcase trimming):
# command line: `--info name-full`


# Pattern listing (trims testcases per suite if they exceed a certain number):
# command line `--info pattern`

# Sample output:

# Primary
# ..Primary::Alpha
# ....Primary::Alpha::test_a
# ....Primary::Alpha::test_b  --tags server
# ...

# Pattern listing (without any testcase trimming):
# command line `--info pattern-full`


# Count listing, just displays total number of suites / testcases per multitest.
# command line `--info count`

# Sample output:

# Primary: (2 suites, 6 testcases)
# Secondary: (1 suite, 102 testcases)


# Here are a couple of more examples that demonstrates how
# the listing operation takes test filters & sorters into account.

# `--info name --patterns Primary`
# `--info name --shuffle all`
# `--info name --shuffle all --patterns Primary`
# `--info pattern --patterns Primary --tags client color=blue`


@test_plan(name="Command Line Listing Example")
def main(plan):

    multi_test_1 = MultiTest(name="Primary", suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name="Secondary", suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
