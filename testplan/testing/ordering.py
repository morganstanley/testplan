"""
Classes for sorting test context before a test run.

Warning: `sort_instances` functionality is not supported yet, but the
API is available for future compatibility.
"""
import operator
import random
from enum import Enum

from testplan.common.utils.convert import make_tuple


class SortType(Enum):
    """Helper enum used by sorter classes."""

    ALL = "all"
    INSTANCES = "instances"
    SUITES = "suites"
    TEST_CASES = "testcases"

    @classmethod
    def validate(cls, value, allow_tuple=True):
        """
        Valid examples:

            all
            instances
            (suites, instances)
        """

        def validate_single(v):
            if isinstance(v, str):
                return SortType(v.lower()).value
            if isinstance(v, SortType):
                return v.value
            raise ValueError("Invalid shuffle type value: {}".format(v))

        if isinstance(value, (tuple, list)) and allow_tuple:
            values = [validate_single(v) for v in value]
            if SortType.ALL.value in values and len(values) > 1:
                raise ValueError(
                    "Passing extra shuffle types along with"
                    " `all` is a redundant operation. values = {}".format(
                        values
                    )
                )
            return values
        return validate_single(value)


class BaseSorter:
    """Base sorter class"""

    def should_sort_instances(self):
        raise NotImplementedError

    def should_sort_testsuites(self):
        raise NotImplementedError

    def should_sort_testcases(self):
        raise NotImplementedError

    def sort_instances(self, instances):
        raise NotImplementedError

    def sort_testsuites(self, testsuites):
        raise NotImplementedError

    def sort_testcases(self, testcases, param_groups=None):
        raise NotImplementedError

    def sorted_instances(self, instances):
        if self.should_sort_instances():
            return self.sort_instances(instances)
        return instances

    def sorted_testsuites(self, testsuites):
        if self.should_sort_testsuites():
            return self.sort_testsuites(testsuites)
        return testsuites

    def sorted_testcases(self, testsuite, testcases):
        if self.should_sort_testcases():
            test_methods, param_groups = [], {}
            for testcase in testcases:
                param_template = getattr(
                    testcase, "_parametrization_template", None
                )
                if param_template:
                    if param_template not in param_groups:
                        test_methods.append(getattr(testsuite, param_template))
                    param_groups.setdefault(param_template, []).append(
                        testcase
                    )
                else:
                    test_methods.append(testcase)

            result = self.sort_testcases(test_methods, param_groups)
            if isinstance(result, (tuple, list)):
                sorted_test_methods, soted_param_groups = result
            else:
                sorted_test_methods, soted_param_groups = result, {}

            testcases = []
            for test_method in sorted_test_methods:
                if getattr(test_method, "__parametrization_template__", False):
                    testcases.extend(soted_param_groups[test_method.__name__])
                else:
                    testcases.append(test_method)

        return testcases


class NoopSorter(BaseSorter):
    """Sorter that returns the original ordering."""

    def should_sort_instances(self):
        return False

    def should_sort_testsuites(self):
        return False

    def should_sort_testcases(self):
        return False


class TypedSorter(BaseSorter):
    """
    Base sorter that allows configuration of
    sort levels via `sort_type` argument.
    """

    def __init__(self, sort_type=SortType.ALL):
        self.sort_types = set(make_tuple(SortType.validate(sort_type)))
        self.sort_all = SortType.ALL.value in self.sort_types

    def check_sort_type(self, sort_type):
        return self.sort_all or sort_type.value in self.sort_types

    def should_sort_instances(self):
        return self.check_sort_type(SortType.INSTANCES)

    def should_sort_testsuites(self):
        return self.check_sort_type(SortType.SUITES)

    def should_sort_testcases(self):
        return self.check_sort_type(SortType.TEST_CASES)


class ShuffleSorter(TypedSorter):
    """
    Sorter that shuffles the ordering. It is idempotent in a way that,
    it will return the same ordering for the same seed for the
    same list.
    """

    def __init__(self, shuffle_type=SortType.ALL, seed=None):
        self.seed = seed or random.randint(0, 1000)
        super(ShuffleSorter, self).__init__(sort_type=shuffle_type)

    @property
    def randomizer(self):
        return random.Random(self.seed)

    def shuffle(self, items):
        items_copy = list(items)
        self.randomizer.shuffle(items_copy)
        return items_copy

    def sort_instances(self, instances):
        return self.shuffle(instances)

    def sort_testsuites(self, testsuites):
        return self.shuffle(testsuites)

    def sort_testcases(self, testcases, param_groups=None):
        param_groups = param_groups or {}
        return self.shuffle(testcases), {
            param_template: self.shuffle(testcases)
            for param_template, testcases in param_groups.items()
        }


class AlphanumericSorter(TypedSorter):
    """Sorter that uses basic alphanumeric ordering."""

    def sort_instances(self, instances):
        return sorted(instances, key=operator.attrgetter("name"))

    def sort_testsuites(self, testsuites):
        return sorted(testsuites, key=operator.attrgetter("name"))

    def sort_testcases(self, testcases, param_groups=None):
        param_groups = param_groups or {}
        return sorted(testcases, key=operator.attrgetter("name")), {
            param_template: sorted(testcases, key=operator.attrgetter("name"))
            for param_template, testcases in param_groups.items()
        }
