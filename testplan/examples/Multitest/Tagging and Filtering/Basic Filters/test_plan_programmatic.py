"""
This example shows:

* How the test cases and test suites can be tagged.

* How tests / suites/ testcases can be filtered
  by patterns and tags programmatically.

"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.filtering import Filter, Pattern, Tags, TagsAll


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


# Default (noop) filter, runs all tests
default_filter = Filter()

# Run all Multitest named `Primary` and all of its suites & testcases.
pattern_filter_1 = Pattern('Primary')

# Run `Alpha` suite (and all testcases) from `Primary` multitest.
pattern_filter_2 = Pattern('Primary:Alpha')

# Run `Alpha.test_1` from `Primary` multitest.
pattern_filter_3 = Pattern('Primary:Alpha:test_1')

# Run all testcases named `test_1` from all suites & multitests.
pattern_filter_4 = Pattern('*:*:test_1')

# Multi-pattern filtering, runs multitests with names `Primary` and `Secondary`
pattern_filter_5 = Pattern.any('Primary', 'Secondary')

# Run all multitests that end with `ary` (Primary & Secondary)
pattern_filter_6 = Pattern('*ary')

# Tag based filtering, runs all testcases that are tagged with `server`.
# Suite level tags propagate to testcases as well.
tag_filter_1 = Tags('server')

# Run all testcases with the named tag: `color = blue`
tag_filter_2 = Tags({'color': 'blue'})

# Multi tag filtering, run all testcases tagged with `server` OR `client`.
tag_filter_3 = Tags(('server', 'client'))

# Multi tag filtering, run all testcases tagged with
#  `server` OR `color = red` OR `color = blue`
tag_filter_4 = Tags({'simple': 'server', 'color': ('red', 'blue')})

# Multi tag filtering, run all testcases tagged with `server` AND `client`.
tag_filter_5 = TagsAll(('server', 'client'))

# Replace the `test_filter` argument with the
# filters declared above to see how they work.

@test_plan(
    name='Tagging & Filtering (Programmatic)',
    test_filter=default_filter,
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style('testcase', 'testcase')
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary', suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name='Secondary', suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
