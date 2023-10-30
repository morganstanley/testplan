"""Filtering logic for Multitest, Suites and testcase methods (of Suites)"""

import argparse
import collections
import fnmatch
import operator
import re
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Callable, List, Type

from testplan.testing import tagging
from testplan.testing.common import TEST_PART_PATTERN_REGEX

if TYPE_CHECKING:
    from testplan.testing.base import Test


class FilterLevel(Enum):
    """
    This enum is used by test classes (e.g. `~testplan.testing.base.Test`)
    to declare the depth of filtering logic while ``filter`` method is run.

    By default only ``test`` (e.g. top) level filtering is used.
    """

    TEST = "test"
    TESTSUITE = "testsuite"
    TESTCASE = "testcase"


class FilterCategory(IntEnum):
    COMMON = auto()
    PATTERN = auto()
    TAG = auto()


class BaseFilter:
    """
    Base class for filters, supports bitwise
    operators for composing multiple filters.

    e.g. (FilterA(...) & FilterB(...)) | ~FilterC(...)
    """

    def filter(self, test, suite, case) -> bool:
        raise NotImplementedError

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)

    def __invert__(self):
        return Not(self)


class Filter(BaseFilter):
    """
    Noop filter class, users can inherit from
    this to implement their own filters.

    Returns True by default for all filtering operations,
    implicitly checks for test instances ``filter_levels`` declaration
    to apply the filtering logic.
    """

    category = FilterCategory.COMMON

    def filter_test(self, test) -> bool:
        return True

    def filter_suite(self, suite) -> bool:
        return True

    def filter_case(self, case) -> bool:
        return True

    def filter(self, test, suite, case):
        res = True
        for level in test.get_filter_levels():
            if level is FilterLevel.TEST:
                res = res and self.filter_test(test)
            elif level is FilterLevel.TESTSUITE:
                res = res and self.filter_suite(suite)
            elif level is FilterLevel.TESTCASE:
                res = res and self.filter_case(case)
            if not res:
                return False
        return True


def flatten_filters(
    metafilter_kls: Type["MetaFilter"], filters: List["Filter"]
) -> List[Filter]:
    """
    This is used for flattening nested filters of same type

    So when we have something like:

        Or(filter-1, filter-2) | Or(filter-3, filter-4)

    We end up with:

        Or(filter-1, filter-2, filter-3, filter-4)

    Instead of:

        Or(Or(filter-1, filter-2), Or(filter-3, filter-4))
    """
    result = []
    for f in filters:
        # Flatten if exact class, but not subclass
        if type(f) == metafilter_kls:
            result.extend(flatten_filters(metafilter_kls, f.filters))
        else:
            result.append(f)
    return result


class MetaFilter(BaseFilter):
    """Higher level filter that allow composition of other filters."""

    operator_str = None

    def __init__(self, *filters):
        self.filters = flatten_filters(self.__class__, filters)

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__, ", ".join([repr(f) for f in self.filters])
        )

    def __str__(self):
        delimiter = " {} ".format(self.operator_str)
        return "({})".format(
            delimiter.join([str(filter_obj) for filter_obj in self.filters])
        )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and other.filters == self.filters
        )

    def composed_filter(self, _test, _suite, _case) -> bool:
        raise NotImplementedError

    def filter(self, test, suite, case):
        return self.composed_filter(test, suite, case)


class Or(MetaFilter):
    """
    Meta filter that returns True if ANY of the child filters return True.
    """

    operator_str = "|"

    def composed_filter(self, test, suite, case):
        return any(f.filter(test, suite, case) for f in self.filters)


class And(MetaFilter):
    """
    Meta filter that returns True if ALL of the child filters return True.
    """

    operator_str = "&"

    def composed_filter(self, test, suite, case):
        return all(f.filter(test, suite, case) for f in self.filters)


class Not(BaseFilter):
    """Meta filter that returns the inverse of the original filter result."""

    def __init__(self, filter_obj):
        self.filter_obj: Filter = filter_obj

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.filter_obj)

    def __invert__(self):
        """Double negative returns original filter."""
        return self.filter_obj

    def __eq__(self, other):
        return isinstance(other, Not) and other.filter_obj == self.filter_obj

    def filter(self, test, suite, case):
        return not self.filter_obj.filter(test, suite, case)


class BaseTagFilter(Filter):
    """Base filter class for tag based filtering."""

    category = FilterCategory.TAG

    def __init__(self, tags):
        self.tags_orig = tags
        self.tags = tagging.validate_tag_value(tags)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.tags_orig == other.tags_orig
        )

    def __repr__(self):
        return '{}(tags="{}")'.format(self.__class__.__name__, self.tags_orig)

    def get_match_func(self) -> Callable:
        raise NotImplementedError

    def _check_tags(self, obj, tag_getter) -> bool:
        return self.get_match_func()(
            tag_arg_dict=self.tags, target_tag_dict=tag_getter(obj)
        )

    def filter_test(self, test):
        return self._check_tags(
            obj=test, tag_getter=operator.methodcaller("get_tags_index")
        )

    def filter_suite(self, suite):
        return self._check_tags(
            obj=suite, tag_getter=operator.attrgetter("__tags_index__")
        )

    def filter_case(self, case):
        return self._check_tags(
            obj=case, tag_getter=operator.attrgetter("__tags_index__")
        )


class Tags(BaseTagFilter):
    """Tag filter that returns True if ANY of the given tags match."""

    def get_match_func(self):
        return tagging.check_any_matching_tags


class TagsAll(BaseTagFilter):
    """Tag filter that returns True if ALL of the given tags match."""

    def get_match_func(self):
        return tagging.check_all_matching_tags


class Pattern(Filter):
    """
    Base class for name based, glob style filtering.

    https://docs.python.org/3.4/library/fnmatch.html

    Examples:

        <Multitest name>:<suite name>:<testcase name>
        <Multitest name>:*:<testcase name>
        *:<suite name>:*
    """

    MAX_LEVEL = 3
    ALL_MATCH = "*"

    category = FilterCategory.PATTERN

    def __init__(self, pattern, match_uid=False):
        self.pattern = pattern
        self.match_uid = match_uid
        self.parse_pattern(pattern)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.pattern == other.pattern
            and self.match_uid == other.match_uid
        )

    def __repr__(self):
        return '{}(pattern="{}")'.format(self.__class__.__name__, self.pattern)

    def parse_pattern(self, pattern: str) -> List[str]:
        # ":" or "::" can be used as delimiter
        patterns = (
            pattern.split("::") if "::" in pattern else pattern.split(":")
        )

        if len(patterns) > self.MAX_LEVEL:
            raise ValueError(
                "Maximum filtering level ({}) exceeded: {}".format(
                    self.MAX_LEVEL, pattern
                )
            )

        test_level, suite_level, case_level = patterns + (
            [self.ALL_MATCH] * (self.MAX_LEVEL - len(patterns))
        )

        # structural pattern for test level
        m = re.match(TEST_PART_PATTERN_REGEX, test_level)
        if m:
            test_name_p = m.group(1)
            test_cur_part_p = m.group(2)
            test_ttl_part_p = m.group(3)

            try:
                test_cur_part_p_, test_ttl_part_p_ = int(test_cur_part_p), int(
                    test_ttl_part_p
                )
            except ValueError:
                pass
            else:
                if test_ttl_part_p_ <= test_cur_part_p_:
                    raise ValueError(
                        f"Meaningless part specified for {test_name_p}, "
                        f"we cannot cut a pizza by {test_ttl_part_p_} and then take "
                        f"the {test_cur_part_p_}-th slice, and we count from 0."
                    )
            self.test_pattern = (
                test_name_p,
                (test_cur_part_p, test_ttl_part_p),
            )
        else:
            self.test_pattern = test_level

        self.suite_pattern = suite_level
        self.case_pattern = case_level

    def filter_test(self, test: "Test"):
        # uid and structural pattern may differ under certain circumstances
        if self.match_uid:
            return fnmatch.fnmatch(test.uid(), self.test_pattern)

        if isinstance(self.test_pattern, tuple):
            if not hasattr(test.cfg, "part"):
                return False

            name_p, (cur_part_p, ttl_part_p) = self.test_pattern
            cur_part: int
            ttl_part: int
            cur_part, ttl_part = test.cfg.part or (0, 1)
            return (
                fnmatch.fnmatch(test.name, name_p)
                and fnmatch.fnmatch(str(cur_part), cur_part_p)
                and fnmatch.fnmatch(str(ttl_part), ttl_part_p)
            )

        return fnmatch.fnmatch(test.name, self.test_pattern)

    def filter_suite(self, suite):
        # For test suite uid is the same as name
        return fnmatch.fnmatch(suite.name, self.suite_pattern)

    def filter_case(self, case):
        name_match = fnmatch.fnmatch(
            case.__name__ if self.match_uid else case.name,
            self.case_pattern,
        )

        # Check if the testcase is parametrized - if so, we also consider
        # the filter to match if the parametrization template is matched.
        parametrization_template = getattr(
            case, "_parametrization_template", None
        )
        if parametrization_template:
            param_match = fnmatch.fnmatch(
                parametrization_template, self.case_pattern
            )
            return name_match or param_match

        return name_match

    @classmethod
    def any(cls, *patterns: str):
        """
        Shortcut for filtering against multiple patterns.

        e.g. Pattern.any(<pattern 1>, <pattern 2>...)
        """
        return Or(*[Pattern(pattern=pattern) for pattern in patterns])


class PatternAction(argparse.Action):
    """
    Parser action for generating Pattern filters.
    Returns a list of `Pattern` filter objects.

    In:

    .. code-block:: bash

        --patterns foo bar --patterns baz

    Out:

    .. code-block:: python

        [Pattern('foo'), Pattern('bar'), Pattern('baz')]
    """

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []

        items.extend([Pattern(value) for value in values])
        setattr(namespace, self.dest, items)


class TagsAction(argparse.Action):
    """
    Parser action for generating tags (any) filters.

    In:

    .. code-block:: bash

        --tags foo bar hello=world --tags baz hello=mars

    Out:

    .. code-block:: python

        [
            Tags({
                'simple': {'foo', 'bar'},
                'hello': {'world'},
            }),
            Tags({
                'simple': {'baz'},
                'hello': {'mars'},
            })
        ]
    """

    filter_class = Tags

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.append(self.filter_class(tagging.parse_tag_arguments(*values)))
        setattr(namespace, self.dest, items)


class TagsAllAction(TagsAction):
    """
    Parser action for generating tags (all) filters.

    In:

    .. code-block:: bash

        --tags-all foo bar hello=world --tags-all baz hello=mars

    Out:

    .. code-block:: python

        [
            TagsAll({
                'simple': {'foo', 'bar'},
                'hello': {'world'},
            }),
            TagsAll({
                'simple': {'baz'},
                'hello': {'mars'},
            })
        ]
    """

    filter_class = TagsAll


def parse_filter_args(parsed_args, arg_names):
    """
    Utility function that's used for grouping filters of the same category
    together. Will be used while parsing command line arguments for
    test filters.

    Filters that belong to the same category will be grouped under `Or`
    whereas filters of different categories will be grouped under `And`.

    In:

    .. code-block:: bash

        --patterns my_pattern --tags foo --tags-all bar baz

    Out:

    .. code-block:: python

        And(
            Pattern('my_pattern'),
            Or(
                Tags({'simple': {'foo'}}),
                TagsAll({'simple': {'bar', 'baz'}}),
            )
        )
    """

    def get_filter_category(filter_objs):
        if len(filter_objs) == 1:
            return filter_objs[0]
        return Or(*filter_objs)

    filter_dict = collections.defaultdict(list)

    for arg_name in arg_names:
        filters = parsed_args.get(arg_name)
        if filters:
            filter_dict[filters[0].category].extend(filters)

    # no arg_names are passed or parsed args is empty
    if not filter_dict:
        return None

    elif len(filter_dict) == 1:
        values = list(filter_dict.values())
        return get_filter_category(values[0])

    return And(
        *[get_filter_category(filters) for filters in filter_dict.values()]
    )
