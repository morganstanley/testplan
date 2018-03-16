"""
    This example shows how the suites / test cases
    of a test plan can be listed programmatically.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.testing import listing, filtering


@testsuite
class Alpha(object):

    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags='server')
    def test_b(self, env, result):
        pass

    @testcase(tags={'color': 'blue'})
    def test_c(self, env, result):
        pass


@testsuite(tags='server')
class Beta(object):

    @testcase(tags='client')
    def test_a(self, env, result):
        pass

    @testcase(tags={'color': 'red'})
    def test_b(self, env, result):
        pass

    @testcase(tags={'color': ('blue', 'yellow')})
    def test_c(self, env, result):
        pass


@testsuite(tags='client')
class Gamma(object):

    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags={'color': ('yellow', 'red')})
    def test_b(self, env, result):
        pass

    @testcase(parameters=list(range(100)))
    def test_c(self, env, result, val):
        pass


# A test lister object prevents Testplan from running tests, but instead
# prints out information (list tests, counts etc) about your test setup.

# You can trigger this functionality by passing an instance of test lister
# as `test_lister` argument to `@test_plan' decorator.


# Default lister, lists by names
name_lister = listing.NameLister()

# Sample output:

# Primary
# ..Alpha
# ....test_a
# ....test_b
# ...

# Like NameLister, but does not trim testcases. May produce
# large output in case of parametrization

expanded_name_lister = listing.ExpandedNameLister()


# Pattern lister, lists tests in a format that is compatible with
# `--patterns` / `--tags` / `--tags-all` arguments
pattern_lister = listing.PatternLister()

# Sample output:

# Primary
# ..Primary:Alpha
# ....Primary:Alpha:test_a
# ....Primary:Alpha:test_b  --tags server
# ...


# Like Pattern lister, but does not trim testcases. May produce
# large output in case of parametrization

expanded_pattern_lister = listing.ExpandedPatternLister()

# Count lister, just lists top level test instances with the number of
# suites & testcases.

count_lister = listing.CountLister()

# Sample output:

# Primary: (2 suites, 6 testcases)
# Secondary: (1 suite, 102 testcases)


# Here is a list of filters, you can pass them to
# the test plan declaration below and see how they change the
# test listing output.

pattern_filter_1 = filtering.Pattern('Primary')
pattern_filter_2 = filtering.Pattern('*:*:test_c')

tag_filter_1 = filtering.Tags('client')
tag_filter_2 = filtering.Tags({'color': 'blue'})

composite_filter_1 = pattern_filter_1 | pattern_filter_2
composite_filter_2 = (pattern_filter_1 & tag_filter_1) | tag_filter_2


@test_plan(
    name='Programmatic Listing Example',
    # You can replace this argument with the other listers defined above
    # to see different output formats.
    # test_lister=test_lister,
    test_lister=name_lister,

    # Comment out the arguments below to see how they affect the listing output.
    # test_filter=pattern_filter_1,
    # test_sorter=ordering.ShuffleSorter()
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary',
                             suites=[Alpha(), Beta()])
    multi_test_2 = MultiTest(name='Secondary',
                             suites=[Gamma()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
