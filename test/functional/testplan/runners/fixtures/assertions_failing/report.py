"""Test Multitest - Test Suite - Result - Test Report - Exporter integration"""
import re

from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport

from testplan.testing.multitest.base import Categories

from .suites import always_true, always_false, ERROR_MSG, error_func
from testplan.common.utils.testing import check_iterable


def check_row_comparison_data(expected_data):
    """
        Utility function that can be used for advanced row comparison matching.

        Runs against serialized RowComparison objects.

        Useful for matching traceback patterns etc as well.
    """
    def checker(actual_data):
        try:
            for expected_row, actual_row in zip(expected_data, actual_data):
                idx_a, row_a, diff_a, error_a, extra_a = actual_row
                idx_b, row_e, diff_e, error_e, extra_e = expected_row

                assert idx_a == idx_b, 'Indexes do not' \
                                       ' match: {} != {}'.format(idx_a, idx_b)

                check_iterable(expected=row_e, actual=row_a)
                check_iterable(expected=diff_e, actual=diff_a)
                check_iterable(expected=error_e, actual=error_a)
                check_iterable(expected=extra_e, actual=extra_a)
        except AssertionError:
            return False
        return True
    return checker


def check_xml_tag_comparison_data(expected_data):
    """
        Similar to check_row_comparison_data,
        runs against XMLTagComparison objects.
    """
    def check(actual, expected):
        if callable(expected):
            assert expected(actual) is True, \
                'Custom callable match failed: {}, {}'.format(actual, expected)
        else:
            assert expected == actual

    def checker(actual_data):
        try:
            for expected, actual in zip(expected_data, actual_data):
                tag_a, diff_a, error_a, extra_a = actual
                tag_e, diff_e, error_e, extra_e = expected

                check(tag_a, tag_e)
                check(diff_a, diff_e)
                check(error_a, error_e)
                check(extra_a, extra_e)
        except AssertionError:
            return False
        return True
    return checker


expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyMultitest',
            category=Categories.MULTITEST,
            entries=[
                TestGroupReport(
                    name='MySuite',
                    category=Categories.SUITE,
                    entries=[
                        TestCaseReport(
                            name='test_log',
                            entries=[
                                {
                                    'type': 'Log',
                                    'description': 'hello world'
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_comparison',
                            entries=[
                                {
                                    'first': 1,
                                    'second': 1,
                                    'type': 'Equal',
                                    'passed': True,
                                    'description': 'equality description'
                                },
                                {
                                    'first': 1,
                                    'second': 2,
                                    'type': 'NotEqual',
                                    'passed': True,
                                },
                                {
                                    'first': 1,
                                    'second': 2,
                                    'type': 'Less',
                                    'passed': True,
                                },
                                {
                                    'first': 2,
                                    'second': 1,
                                    'type': 'Greater',
                                    'passed': True,
                                },
                                {
                                    'first': 1,
                                    'second': 2,
                                    'type': 'LessEqual',
                                    'passed': True,
                                },
                                {
                                    'first': 2,
                                    'second': 1,
                                    'type': 'GreaterEqual',
                                    'passed': True
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_approximate_equality',
                            entries=[
                                {
                                    'first': 95,
                                    'second': 100,
                                    'rel_tol': 0,
                                    'abs_tol': 5,
                                    'type': 'IsClose',
                                    'passed': True
                                },
                                {
                                    'first': 99,
                                    'second': 101,
                                    'rel_tol': 0,
                                    'abs_tol': 1,
                                    'type': 'IsClose',
                                    'passed': False
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_membership',
                            entries=[
                                {
                                    'member': 1,
                                    'container': '[1, 2, 3]',
                                    'type': 'Contain',
                                },
                                {
                                    'member': 'foo',
                                    'container': 'bar',
                                    'type': 'NotContain',
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_regex',
                            entries=[
                                {
                                    'type': 'RegexMatch',
                                    'pattern': 'foo',
                                    'string': 'foobar',
                                    'match_indexes': [[0, 3]],
                                    'passed': True,
                                },
                                {
                                    'type': 'RegexMatch',
                                    'pattern': 'foo',
                                    'string': 'bar',
                                    'match_indexes': [],
                                    'passed': False,
                                },
                                {
                                    'type': 'RegexMatchNotExists',
                                    'pattern': 'foo',
                                    'string': 'bar',
                                    'match_indexes': [],
                                    'passed': True,
                                },
                                {
                                    'type': 'RegexMatchNotExists',
                                    'pattern': 'foo',
                                    'string': 'foobar',
                                    'match_indexes': [[0, 3]],
                                    'passed': False,
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_group_assertions',
                            entries=[
                                {
                                    'type': 'Equal',
                                    'first': 'foo',
                                    'second': 'foo',
                                    'passed': True,
                                },
                                {
                                    'type': 'Group',
                                    # because sub group's assertion is failed
                                    'passed': False,
                                    'description':  'assertion '
                                                    'group description',
                                    'entries': [
                                        {
                                            'type': 'Equal',
                                            'first': 1,
                                            'second': 1,
                                            'passed': True,
                                        },
                                        {
                                            'type': 'RegexMatch',
                                            'pattern': 'hello',
                                            'string': 'hello world',
                                            'match_indexes': [[0, 5]],
                                            'passed': True,
                                        },
                                        {
                                            'type': 'Group',
                                            'passed': False,
                                            'description': 'sub group'
                                                           ' description',
                                            'entries': [
                                                {
                                                    'type': 'Equal',
                                                    'first': 'foo',
                                                    'second': 'bar',
                                                    'passed': False,
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_summary_assertions',
                            entries=[
                                {
                                    'type': 'Summary',
                                    'passed': False,
                                    'description':  None,
                                    'entries': [
                                        {
                                            'type': 'Group',
                                            'description': 'Category: DEFAULT',
                                            'passed': False,
                                            'entries': [
                                                {
                                                    'type': 'Group',
                                                    'description': 'Assertion type: Equal',
                                                    'passed': False,
                                                    'entries':[
                                                        {
                                                            'type': 'Group',
                                                            'description': 'DEFAULT - Equal - Failing - Displaying 3 of 100.',
                                                            'passed': False,
                                                            'entries': [
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 0,
                                                                    'second': 1,
                                                                    'passed': False,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 1,
                                                                    'second': 2,
                                                                    'passed': False,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 2,
                                                                    'second': 3,
                                                                    'passed': False,
                                                                },
                                                            ]
                                                        },
                                                        {
                                                            'type': 'Group',
                                                            'passed': True,
                                                            'description': 'DEFAULT - Equal - Passing - Displaying 2 of 100.',
                                                            'entries': [
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 0,
                                                                    'second': 0,
                                                                    'passed': True,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 1,
                                                                    'second': 1,
                                                                    'passed': True,
                                                                }
                                                            ]
                                                        },
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='testcase_level_summarization',
                            entries=[
                                {
                                    'type': 'Summary',
                                    'passed': False,
                                    'description':  None,
                                    'entries': [
                                        {
                                            'type': 'Group',
                                            'description': 'Category: DEFAULT',
                                            'passed': False,
                                            'entries': [
                                                {
                                                    'type': 'Group',
                                                    'description': 'Assertion type: Equal',
                                                    'passed': False,
                                                    'entries':[
                                                        {
                                                            'type': 'Group',
                                                            'description': 'DEFAULT - Equal - Failing - Displaying 3 of 100.',
                                                            'passed': False,
                                                            'entries': [
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 0,
                                                                    'second': 1,
                                                                    'passed': False,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 1,
                                                                    'second': 2,
                                                                    'passed': False,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 2,
                                                                    'second': 3,
                                                                    'passed': False,
                                                                },
                                                            ]
                                                        },
                                                        {
                                                            'type': 'Group',
                                                            'passed': True,
                                                            'description': 'DEFAULT - Equal - Passing - Displaying 2 of 100.',
                                                            'entries': [
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 0,
                                                                    'second': 0,
                                                                    'passed': True,
                                                                },
                                                                {
                                                                    'type': 'Equal',
                                                                    'first': 1,
                                                                    'second': 1,
                                                                    'passed': True,
                                                                }
                                                            ]
                                                        },
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_exception_assertions',
                            entries=[
                                {
                                    'type': 'ExceptionRaised',
                                    'description': 'key error description',
                                    'passed': True,
                                },
                                {
                                    'type': 'ExceptionNotRaised',
                                    'passed': False,
                                },
                                {
                                    'type': 'ExceptionRaised',
                                    'pattern': 'hello',
                                    'passed': True,
                                },
                                {
                                    'type': 'ExceptionRaised',
                                    'func': lambda val: re.match(
                                        '<function[\w\s\.<>]+>', val),
                                    'passed': True,
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_equal_slices_assertions',
                            entries=[
                                {
                                    'type': 'EqualSlices',
                                    'description': 'passing equal slices',
                                    'data': [
                                        # Corresponds to a
                                        # serialized SliceComparison object
                                        (
                                            # slice
                                            repr(slice(2, None)),
                                            # comparison indices
                                            [2, 3],
                                            # mismatch indices
                                            [],
                                            # actual
                                            [3, 4],
                                            # expected
                                            [3, 4],
                                        )
                                    ],
                                    'passed': True,
                                },
                                {
                                    'type': 'EqualSlices',
                                    'passed': False,
                                },
                                {
                                    'type': 'EqualExcludeSlices',
                                    'description': 'passing equal'
                                                   ' exclude slices',
                                    'passed': True,
                                },
                                {
                                    'type': 'EqualExcludeSlices',
                                    'passed': False,
                                    'data': [
                                        (
                                            repr(slice(2, 4)),
                                            [0, 1],
                                            [0, 1],
                                            [1, 2],
                                            ['a', 'b']
                                        )
                                    ],
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_column_contain',
                            entries=[
                                {
                                    'type': 'ColumnContain',
                                    'description': 'column contain passing',
                                    'data': [
                                        (0, 1, True),
                                        (1, 10, True),
                                        (2, 30, True),
                                    ],
                                    'column': 'foo',
                                    'values': [1, 5, 10, 30, 50],
                                    'limit': 3,
                                    'passed': True,
                                },
                                {
                                    'type': 'ColumnContain',
                                    'passed': False,
                                    'data': [
                                        (3, 0, False),
                                        (4, 100, False),
                                    ],
                                    'values': [1, 5, 10, 30, 50],
                                    'limit': 2,
                                    'column': 'foo',
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_table_match',
                            entries=[
                                {
                                    'type': 'TableMatch',
                                    'description': 'basic table match',
                                    'columns': ['name', 'value'],
                                    'include_columns': None,
                                    'exclude_columns': None,
                                    'message': None,
                                    'passed': True,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (3, ['ddd', 4], {}, {}, {}),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'passed': True,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            {}, {},
                                            {'name': always_true.__name__}
                                        ),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'passed': True,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            {}, {},
                                            {'name': 'REGEX(d+)'}
                                        ),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name', 'value'],
                                    'passed': False,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            # diff populated
                                            {'name': 'xxx'}, {}, {}
                                        ),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'passed': False,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            {'name': always_false.__name__},
                                            {}, {}
                                        ),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'passed': False,
                                    'data': [
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            {'name': 'REGEX(zzz)'},
                                            {}, {}
                                        ),
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'passed': False,
                                    'data': check_row_comparison_data([
                                        (0, ['aaa', 1], {}, {}, {}),
                                        (1, ['bbb', 2], {}, {}, {}),
                                        (2, ['ccc', 3], {}, {}, {}),
                                        (
                                            3,
                                            ['ddd', 4],
                                            {},
                                            # Check traceback msg
                                            {'name': lambda v: ERROR_MSG in v},
                                            {}
                                        ),
                                    ])
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name'],
                                    'include_columns': ['name'],
                                    'passed': True,
                                    'data': [
                                        (0, ['aaa'], {}, {}, {}),
                                        (1, ['bbb'], {}, {}, {}),
                                        (2, ['ccc'], {}, {}, {}),
                                        (3, ['ddd'], {}, {}, {})
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name', 'value', 'is_finished'],
                                    'include_columns': ['name'],
                                    'passed': True,
                                    'data': [
                                        (
                                            0,
                                            ['aaa', 10, True],
                                            {}, {}, {'value': 1}
                                        ),
                                        (
                                            1,
                                            ['bbb', 20, False],
                                            {}, {}, {'value': 2}
                                        ),
                                        (
                                            2,
                                            ['ccc', 30, True],
                                            {}, {}, {'value': 3}
                                        ),
                                        (
                                            3,
                                            ['ddd', 40, False],
                                            {}, {}, {'value': 4}
                                        )
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name'],
                                    'exclude_columns': ['value', 'is_finished'],
                                    'passed': True,
                                    'data': [
                                        (0, ['aaa'], {}, {}, {}),
                                        (1, ['bbb'], {}, {}, {}),
                                        (2, ['ccc'], {}, {}, {}),
                                        (3, ['ddd'], {}, {}, {})
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name', 'value', 'is_finished'],
                                    'exclude_columns': ['value', 'is_finished'],
                                    'passed': True,
                                    'data': [
                                        (
                                            0,
                                            ['aaa', 10, True],
                                            {}, {}, {'value': 1}
                                        ),
                                        (
                                            1,
                                            ['bbb', 20, False],
                                            {}, {}, {'value': 2}
                                        ),
                                        (
                                            2,
                                            ['ccc', 30, True],
                                            {}, {}, {'value': 3}
                                        ),
                                        (
                                            3,
                                            ['ddd', 40, False],
                                            {}, {}, {'value': 4}
                                        )
                                    ]
                                },
                                {
                                    'type': 'TableMatch',
                                    'columns': ['name', 'value'],
                                    'include_columns': ['name', 'value'],
                                    'fail_limit': 2,
                                    'passed': False,
                                    'data': [
                                        (
                                            0,
                                            ['aaa', 1],
                                            {'value': 10}, {}, {}
                                        ),
                                        (
                                            2,
                                            ['ccc', 3],
                                            {'value': 30}, {}, {}
                                        ),
                                    ]
                                },
                            ],
                        ),
                        TestCaseReport(
                            name='test_xml_check',
                            entries=[
                                {
                                    'type': 'XMLCheck',
                                    'passed': True,
                                    'xpath': '/Root/Test',
                                    'description': 'basic XML check',
                                    'message': 'xpath: `/Root/Test`'
                                               ' exists in the XML.',
                                    'tags': None,
                                    'namespaces': None,
                                    'data': [],
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': True,
                                    'xpath': '/Root/Test',
                                    'message': None,
                                    'tags': ['Value1', 'Value2'],
                                    'namespaces': None,
                                    'data': [
                                        ['Value1', None, None, None],
                                        ['Value2', None, None, None],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': True,
                                    'data': [
                                        [
                                            'Value1', None, None,
                                            "VAL in ['a', 'b', 'Value1']"
                                        ],
                                        [
                                            'Value2', None, None,
                                            'REGEX(.*lue2)'
                                        ],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': True,
                                    'namespaces': {'a': 'http://testplan'},
                                    'data': [
                                        ['Hello world!', None, None, 'Hello*']
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'xpath': '/Root/Bar',
                                    'message': 'xpath: `/Root/Bar`'
                                               ' does not exist in the XML.'
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': [
                                        ['Foo', None, None, None],
                                        ['Bar', 'Alpha', None, None],
                                        ['Baz', 'Beta', None, None],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': [
                                        [
                                            'Foo', None,
                                            'No value is found,'
                                            ' although the path exists.', None
                                        ],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': [
                                        ['Foo', None, None, None],
                                        [
                                            None,
                                            'Bar',
                                            'No tags found for the index: 1',
                                            None
                                        ],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': [
                                        [
                                            'Value1',
                                            "VAL in ['a', 'b', 'c']",
                                            None,
                                            None,
                                        ],
                                        [
                                            'Value2',
                                            'REGEX(Foo)',
                                            None,
                                            None,
                                        ],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': [
                                        ['Foobar', 'Hello*', None, None],
                                    ]
                                },
                                {
                                    'type': 'XMLCheck',
                                    'passed': False,
                                    'data': check_xml_tag_comparison_data([
                                        [
                                            'Foo',
                                            None,
                                            # Traceback check
                                            lambda v: ERROR_MSG in v,
                                            error_func.__name__
                                        ],
                                    ])
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_dict_check',
                            entries=[
                                {
                                    'type': 'DictCheck',
                                    'passed': True,
                                    'has_keys_diff': [],
                                    'absent_keys_diff': [],
                                    'has_keys': ['foo'],
                                    'absent_keys': ['baz'],
                                    'description': 'basic dict check',
                                },
                                {
                                    'type': 'DictCheck',
                                    'passed': False,
                                    'has_keys_diff': ['baz'],
                                    'absent_keys_diff': ['foo'],
                                    'has_keys': ['bar', 'baz'],
                                    'absent_keys': ['foo', 'bat'],
                                    'description': 'failing dict check'
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_dict_match',
                            entries=[
                                {
                                    'type': 'DictMatch',
                                    'passed': True,
                                    'include_keys': ['foo', 'bar'],
                                    'exclude_keys': ['baz', 'bat'],
                                    'description': 'basic dict match',
                                    'actual_description':
                                        'description for actual',
                                    'expected_description':
                                        'description for expected'
                                },
                                {
                                    'type': 'DictMatch',
                                    'passed': False,
                                    'description': 'simple failing match',
                                },
                                {
                                    'type': 'DictMatch',
                                    'passed': True,
                                    'description':
                                        'match with regex & custom func',
                                },
                                {
                                    'type': 'DictMatch',
                                    'passed': False,
                                    'description':
                                        'failing pattern match',
                                },
                                {
                                    'type': 'DictMatch',
                                    'passed': False,
                                    'description':
                                        'failing comparator func',
                                },
                                {
                                    'type': 'DictMatch',
                                    'passed': False,
                                    'description': 'error func',
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_dict_match_all',
                            entries=[
                                {
                                    'type': 'DictMatchAll',
                                    'passed': True,
                                    'description':
                                        'basic unordered dict match all'
                                },
                                {
                                    'type': 'DictMatchAll',
                                    'passed': False,
                                    'description':
                                        'failing dict match all'
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_fix_check',
                            entries=[
                                {
                                    'type': 'FixCheck',
                                    'passed': True,
                                    'has_keys_diff': [],
                                    'absent_keys_diff': [],
                                    'has_keys': ['foo'],
                                    'absent_keys': ['baz'],
                                    'description': 'basic fix check'
                                },
                                {
                                    'type': 'FixCheck',
                                    'passed': False,
                                    'has_keys_diff': ['baz'],
                                    'absent_keys_diff': ['foo'],
                                    'has_keys': ['bar', 'baz'],
                                    'absent_keys': ['foo', 'bat'],
                                    'description': 'failing fix check'
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_fix_match',
                            entries=[
                                {
                                    'type': 'FixMatch',
                                    'passed': True,
                                    'include_keys': ['foo', 'bar'],
                                    'exclude_keys': ['baz', 'bat'],
                                    'description': 'basic fix match',
                                    'actual_description':
                                        'description for actual',
                                    'expected_description':
                                        'description for expected'
                                },
                                {
                                    'type': 'FixMatch',
                                    'passed': False,
                                    'description': 'simple failing match',
                                },
                                {
                                    'type': 'FixMatch',
                                    'passed': True,
                                    'description':
                                        'match with regex & custom func',
                                },
                                {
                                    'type': 'FixMatch',
                                    'passed': False,
                                    'description':
                                        'failing pattern match',
                                },
                                {
                                    'type': 'FixMatch',
                                    'passed': False,
                                    'description':
                                        'failing comparator func',
                                },
                                {
                                    'type': 'FixMatch',
                                    'passed': False,
                                    'description': 'error func',
                                }
                            ]
                        ),
                        TestCaseReport(
                            name='test_fix_match_all',
                            entries=[
                                {
                                    'type': 'FixMatchAll',
                                    'passed': True,
                                    'description':
                                        'basic unordered fix match all'
                                },
                                {
                                    'type': 'FixMatchAll',
                                    'passed': False,
                                    'description':
                                        'failing fix match all'
                                },
                            ]
                        ),
                    ]
                )
            ]
        ),
    ]
)
