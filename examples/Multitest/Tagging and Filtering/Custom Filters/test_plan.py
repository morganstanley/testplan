#!/usr/bin/env python
"""
This example shows how you can implement custom filtering logic for your tests.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style
from testplan.testing.filtering import Filter, Pattern


def check_priority(value):
    """Validator for priority values."""
    assert (
        isinstance(value, int) and value > 0
    ), "Priority must be positive integer."


def priority(value):
    """Decorator that sets priority value for unbound testcase methods."""
    check_priority(value)

    def wrapper(func):
        func.priority = value
        return func

    return wrapper


class BaseSuite(object):
    """Base suite class for suite level custom filtering demonstration."""

    pass


@testsuite
class Alpha(BaseSuite):
    @priority(1)
    @testcase
    def test_1(self, env, result):
        pass

    @priority(5)
    @testcase
    def test_2(self, env, result):
        pass

    @priority(4)
    @testcase
    def test_3(self, env, result):
        pass


@testsuite
class Beta(BaseSuite):
    @priority(1)
    @testcase
    def test_1(self, env, result):
        pass

    @priority(3)
    @testcase
    def test_2(self, env, result):
        pass

    @testcase
    def test_3(self, env, result):
        pass


@testsuite
class Gamma(object):
    @testcase
    def test_1(self, env, result):
        pass

    @priority(2)
    @testcase
    def test_2(self, env, result):
        pass

    @priority(1)
    @testcase
    def test_3(self, env, result):
        pass


class PriorityFilter(Filter):
    """
    Filters testcases with a priority
    that falls between the given interval.
    """

    def __init__(self, minimum, maximum=None):
        check_priority(minimum)
        if maximum is not None:
            check_priority(maximum)

        self.minimum = minimum
        self.maximum = maximum

    def filter_case(self, case):
        if not hasattr(case, "priority"):
            return False

        if self.maximum is not None:
            return self.minimum <= case.priority <= self.maximum
        return self.minimum <= case.priority


class SubclassFilter(Filter):
    """
    Suite level filter that runs suites
    that inherit from the given base class.
    """

    def __init__(self, base_kls):
        assert isinstance(base_kls, type), (
            "`base_kls` must be of type"
            " `type`, it was: {}".format(type(base_kls))
        )

        self.base_kls = base_kls

    def filter_suite(self, suite):
        return isinstance(suite, self.base_kls)


# Run test cases that have a minimum priority of 5
priority_filter_1 = PriorityFilter(minimum=5)

# Run test cases that have a priority between 1 and 3 (inclusive)
priority_filter_2 = PriorityFilter(minimum=1, maximum=3)

# Run test suites that inherit from BaseSuite class.
subclass_filter = SubclassFilter(BaseSuite)

# Custom filters can be composed as well:

# Run test cases that:
# have a minimum priority of 5
# OR have a priority between 1 and 3 (inclusive)
composed_filter_1 = priority_filter_1 | priority_filter_2


# Run test cases that:
# Belong to a suite that inherits from BaseSuite
# AND (have a minimum priority of 5 OR have a priority between 1 and 3)
composed_filter_2 = subclass_filter & composed_filter_1


# We can also compose custom filters with the built-in filters as well:
# Run test cases that:
# Belong to suites that inherit from BaseSuite
# AND have the name `test_2`
composed_filter_3 = subclass_filter & Pattern("*:*:test_2")


# Replace the `test_filter` argument with the
# filters declared above to see how they work.


@test_plan(
    name="Custom Test Filters",
    test_filter=priority_filter_1,
    # Using testcase level stdout so we can see filtered testcases
    stdout_style=Style("testcase", "testcase"),
)
def main(plan):

    multi_test = MultiTest(name="Sample", suites=[Alpha(), Beta(), Gamma()])

    plan.add(multi_test)


if __name__ == "__main__":
    sys.exit(not main())
