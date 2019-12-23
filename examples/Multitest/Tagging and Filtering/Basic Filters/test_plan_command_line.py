#!/usr/bin/env python
"""
This example shows:

* How the tests, test cases and test suites can be tagged.

* How tests / suites/ testcases can be filtered by
  patterns and tags via command line options.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


# A suite with no tags, will be filtered out if we apply any tag based filters
@testsuite
class Alpha(object):

    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass


# A suite with testcase level tags only.
@testsuite
class Beta(object):

    # A testcase tagged with a simple tag: `server`
    # This is a shortcut notation for {'simple': 'server'}
    @testcase(tags='server')
    def test_1(self, env, result):
        pass

    # A testcase tagged with a named (`color`) tag: `blue`
    @testcase(tags={'color': 'blue'})
    def test_2(self, env, result):
        pass

    # A testcase tagged with both simple and named tag
    @testcase(tags={'simple': 'server', 'color': 'blue'})
    def test_3(self, env, result):
        pass


# A suite with class level tags, these class level tags
#  will be propagated to each test case as well.
@testsuite(tags=('server', 'client'))
class Gamma(object):

    @testcase(tags={'color': 'red'})
    def test_1(self, env, result):
        pass

    @testcase(tags={'color': ('blue', 'red')})
    def test_2(self, env, result):
        pass

    @testcase(tags={'color': 'yellow'})
    def test_3(self, env, result):
        pass


# You can run the current Testplan script with the arguments below to see
# how command line filtering works.


# Run all Multitests named `Primary` and all of its suites & testcases.
# command line: `--patterns Primary`


# Run `Alpha` suite (and all testcases) from `Primary` multitest.
# command line: `--patterns Primary:Alpha`


# Run `Alpha.test_1` from `Primary` multitest.
# command line: `--patterns Primary:Alpha:test_1`


# Run all testcases named `test_1` from all suites & multitests.
# command line: `--patterns '*:*:test_1`


# Multi-pattern filtering, runs multitests with names `Primary` and `Secondary`
# command line: `--patterns Primary Secondary`
# command line (alternative) : --patterns Primary --patterns Secondary


# Run all multitests that end with `ary` (Primary & Secondary)
# command line: --patterns *ary


# Tag based filtering, runs all testcases that are tagged with `server`.
# Suite level tags propagate to testcases as well.
# command line: `--tags server`


# Run all testcases with the named tag: `color = blue`
# command line: `--tags color=blue`


# Multi tag filtering, run all testcases tagged with `server` OR `client`.
# command line: `--tags server client`
# command line (alt.): `--tags server --tags client`


# Multi tag filtering, run all testcases tagged with
#  `server` OR `color = red` OR `color = blue`
# command line: `--tags server color=red,blue
# command line (alt.): `--tags server --tags color=red,blue`
# command line (alt. 2): `--tags server --tags color=red --tags color=blue`


# Multi tag filtering, run all testcases tagged with `server` AND `client`.
# command line: `--tags-all server client`


@test_plan(
    name='Tagging & Filtering (Command line)',
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style('testcase', 'testcase')
)
def main(plan):

    multi_test_1 = MultiTest(
        name='Primary',
        suites=[Alpha(), Beta()],
        tags={'color': 'white'}
    )

    multi_test_2 = MultiTest(name='Secondary', suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
