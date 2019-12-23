#!/usr/bin/env python
"""
This example shows:

* How test filters can be composed by using bitwise
  operators or meta filters programmatically.

* How to build complex filtering logic with filter compositions.

"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.filtering import Pattern, Tags, TagsAll, Not, And, Or


@testsuite
class Alpha(object):

    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass


@testsuite
class Beta(object):

    @testcase(tags='server')
    def test_1(self, env, result):
        pass

    @testcase(tags={'color': 'blue'})
    def test_2(self, env, result):
        pass

    @testcase(tags={'simple': 'server', 'color': 'blue'})
    def test_3(self, env, result):
        pass


@testsuite(tags=('server', 'client'))
class Gamma(object):

    @testcase(tags={'color': 'red'})
    def test_1(self, env, result):
        pass

    @testcase(tags={'color': ('blue', 'green')})
    def test_2(self, env, result):
        pass

    @testcase(tags={'color': 'yellow'})
    def test_3(self, env, result):
        pass


@testsuite
class Delta(object):

    @testcase
    def test_1(self, env, result):
        pass

    @testcase
    def test_2(self, env, result):
        pass


# You can use meta filters or bitwise operators to create filter compositions:

# Bitwise OR operator (`|`) or `Or` meta filter creates a new
# filter that runs tests that pass for any of the composed filters.

# E.g. test_filter_a | test_filter_b == Or(test_filter_a, test_filter_b)

# Run tests tagged with `color = red` OR `color = yellow`
# OR tagged with `server` AND `color = blue`

composite_filter_1_a = Tags({'color': ('red', 'yellow')}) \
                       | TagsAll({'simple': 'server', 'color': 'blue'})

composite_filter_1_b = Or(
    Tags({'color': ('red', 'yellow')}),
    TagsAll({'simple': 'server', 'color': 'blue'})
)


# Run tests that belong to multitest named `Primary` or tagged with `server`
# categories (Pattern, Tag etc) is not supported via cmdline.

composite_filter_2_a = Pattern('Primary') | Tags('server')
composite_filter_2_b = Or(Pattern('Primary'), Tags('server'))


# Bitwise AND operator (`&`) or `And` meta filter creates a new filter that
# runs tests that pass all of the composed filters.

# Run tests that have the name `test_2` and are tagged with `color = blue`

composite_filter_3_a = Pattern('*:*:test_2') & Tags({'color': 'blue'})
composite_filter_3_b = And(Pattern('*:*:test_2'), Tags({'color': 'blue'}))


# Bitwise negation (`~`) or `Not` meta filter creates a new filter that
# runs tests that fail the original filter.

# Run tests that do not have the name `test_1`

composite_filter_4_a = ~Pattern('*:*:test_1')
composite_filter_4_b = Not(Pattern('*:*:test_1'))


# Meta filters can be composed as well, which allow us
# to create complex filtering rules:

# Run all tests: tagged with `server`
# AND (belong to `Gamma` multitest OR has the name `test_3`)

composite_filter_5_a = Tags('server') & (
    Pattern('Gamma') | Pattern('*:*:test_3'))

composite_filter_5_b = And(
    Tags('server'),
    Or(
        Pattern('Gamma'),
        Pattern('*:*:test_3')
    )
)

# Run all testcases except the ones that are tagged
# with `color = blue` OR has the name `test_1`.

composite_filter_6_a = ~(Tags({'color': 'blue'}) | Pattern('*:*:test_1'))
composite_filter_6_b = Not(
    Or(
        Tags({'color': 'blue'}),
        Pattern('*:*:test_1')
    )
)


# Replace the `test_filter` argument with the
# filters declared above to see how they work.

@test_plan(
    name='Composite Filters (Programmatic)',
    test_filter=composite_filter_1_a,
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style('testcase', 'testcase')
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary', suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name='Secondary', suites=[Gamma()])
    multi_test_3 = MultiTest(name='Other', suites=[Delta()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)
    plan.add(multi_test_3)


if __name__ == '__main__':
    sys.exit(not main())
