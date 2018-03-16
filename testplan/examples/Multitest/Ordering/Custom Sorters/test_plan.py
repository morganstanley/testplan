"""
This example shows how to implement a custom sorter class.
"""
import operator
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.multitest.suite import get_testsuite_name
from testplan.testing.ordering import NoopSorter, TypedSorter


@testsuite
class Alpha(object):

    @testcase
    def test_a(self, env, result):
        pass

    @testcase
    def test_ab(self, env, result):
        pass


@testsuite
class Beta(object):

    @testcase
    def test_a(self, env, result):
        pass

    @testcase
    def test_ab(self, env, result):
        pass

    @testcase
    def test_abc(self, env, result):
        pass


@testsuite
class Epsilon(object):

    @testcase
    def test_a(self, env, result):
        pass

    @testcase
    def test_ab(self, env, result):
        pass

    @testcase
    def test_abc(self, env, result):
        pass


# We inherit from TypedSorter so we can apply
# optional sorting per group (testcases, testsuites etc)
class ReverseNameLengthSorter(TypedSorter):
    """
        This sorter sorts tests from longest name length to shortest.
    """

    def reverse_sort_by_name(self, items, name_getter):
        return sorted(
            items,
            reverse=True,
            key=lambda item: len(name_getter(item)))

    # We override sort functions for each sort case:
    # Multitests -> sort_instances
    # Test Suites -> sort_testsuites
    # Test cases -> sort_testcases
    def sort_instances(self, instances):
        return self.reverse_sort_by_name(
            instances, operator.attrgetter('name'))

    def sort_testsuites(self, testsuites):
        return self.reverse_sort_by_name(
            testsuites, get_testsuite_name)

    def sort_testcases(self, testcases):
        return self.reverse_sort_by_name(
            testcases, operator.attrgetter('__name__'))


noop_sorter = NoopSorter()

custom_sorter_1 = ReverseNameLengthSorter(sort_type='testcases')

custom_sorter_2 = ReverseNameLengthSorter(
    sort_type=('suites', 'testcases'))


# Replace the `test_sorter` argument with the
# custom sorters declared above to see how they work.
@test_plan(
    name='Custom Sorter Example',
    test_sorter=noop_sorter,
    # Using testcase level stdout so we can see sorted testcases
    stdout_style=Style('testcase', 'testcase')
)
def main(plan):

    multi_test_1 = MultiTest(
        name='Primary',
        suites=[Alpha(), Beta(), Epsilon()])

    plan.add(multi_test_1)


if __name__ == '__main__':
    sys.exit(not main())
