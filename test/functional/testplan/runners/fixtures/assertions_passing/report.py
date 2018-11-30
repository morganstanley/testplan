"""Test Multitest - Test Suite - Result - Test Report - Exporter integration"""
import re

from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport

from testplan.testing.multitest.base import Categories

from .suites import always_true


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
                                    'message': 'hello world',
                                    'description': None
                                },
                                {
                                    'type': 'Log',
                                    'message': 'hello python',
                                    'description': 'log description'
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
                                }
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
                                    'type': 'RegexMatchNotExists',
                                    'pattern': 'foo',
                                    'string': 'bar',
                                    'match_indexes': [],
                                    'passed': True,
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
                                    'passed': True,
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
                                            'passed': True,
                                            'description': 'sub group'
                                                           ' description',
                                            'entries': [
                                                {
                                                    'type': 'Equal',
                                                    'first': 'foo',
                                                    'second': 'foo',
                                                    'passed': True,
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
                                    'passed': True,
                                    'description':  None,
                                    'entries': [
                                        {
                                            'type': 'Group',
                                            'description': 'Category: DEFAULT',
                                            'passed': True,
                                            'entries': [
                                                {
                                                    'type': 'Group',
                                                    'description': 'Assertion type: Equal',
                                                    'passed': True,
                                                    'entries':[
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
                                    'passed': True,
                                    'description':  None,
                                    'entries': [
                                        {
                                            'type': 'Group',
                                            'description': 'Category: DEFAULT',
                                            'passed': True,
                                            'entries': [
                                                {
                                                    'type': 'Group',
                                                    'description': 'Assertion type: Equal',
                                                    'passed': True,
                                                    'entries':[
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
                                    'passed': True,
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
                                    'type': 'EqualExcludeSlices',
                                    'description': 'passing equal'
                                                   ' exclude slices',
                                    'passed': True,
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='test_diff_assertions',
                            entries=[
                                {
                                    'type': 'LineDiff',
                                    'description': 'no difference found',
                                    'first': ['abc\n', 'xyz\n'],
                                    'second': ['abc\n', 'xyz\n'],
                                    'ignore_space_change': False,
                                    'ignore_whitespaces': False,
                                    'ignore_blank_lines': False,
                                    'unified': False,
                                    'context': False,
                                    'passed': True
                                },
                                {
                                    'type': 'LineDiff',
                                    'description': 'no difference found'
                                                   ' with option -b',
                                    'first': ['abc \n', 'xy z\n'],
                                    'second': ['abc\r\n', 'xy\tz\r\n'],
                                    'ignore_space_change': True,
                                    'ignore_whitespaces': False,
                                    'ignore_blank_lines': False,
                                    'unified': False,
                                    'context': True,
                                    'passed': True
                                },
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
                            ],
                        ),
                        TestCaseReport(
                            name='test_table_diff',
                            entries=[
                                {
                                    'type': 'TableDiff',
                                    'description': 'basic table diff',
                                    'columns': ['name', 'value'],
                                    'include_columns': None,
                                    'exclude_columns': None,
                                    'message': None,
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'columns': ['name'],
                                    'include_columns': ['name'],
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'columns': ['name', 'value', 'is_finished'],
                                    'include_columns': ['name'],
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'columns': ['name'],
                                    'exclude_columns': ['value', 'is_finished'],
                                    'passed': True,
                                    'data': []
                                },
                                {
                                    'type': 'TableDiff',
                                    'columns': ['name', 'value', 'is_finished'],
                                    'exclude_columns': ['value', 'is_finished'],
                                    'passed': True,
                                    'data': []
                                },
                            ],
                        ),
                        TestCaseReport(
                            name='test_table_log',
                            entries=[
                                {
                                    'type': 'TableLog',
                                    'description': 'basic table log',
                                    'columns': ['name', 'value'],
                                    'indices': [0, 1, 2, 3],
                                    'display_index': False,
                                    'table': [
                                        {'name': 'aaa', 'value': 1},
                                        {'name': 'bbb', 'value': 2},
                                        {'name': 'ccc', 'value': 3},
                                        {'name': 'ddd', 'value': 4},
                                    ]
                                },
                                {
                                    'type': 'TableLog',
                                    'columns': ['name', 'value'],
                                    'indices': [0, 1, 2, 3],
                                    'display_index': True,
                                    'table': [
                                        {'name': 'aaa', 'value': 1},
                                        {'name': 'bbb', 'value': 2},
                                        {'name': 'ccc', 'value': 3},
                                        {'name': 'ddd', 'value': 4},
                                    ]
                                },
                            ]
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
                                    'passed': True,
                                    'description':
                                        'match with regex & custom func',
                                },
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
                            ]
                        ),
                        TestCaseReport(
                            name='test_dict_log',
                            entries=[
                                {
                                    'type': 'DictLog',
                                    'flattened_dict': [],
                                    'description': 'Log an empty dictionary'
                                },
                                {
                                    'type': 'DictLog',
                                    'flattened_dict': [
                                        [0, 'alpha', ''],
                                        [0, '', ('str', 'foobar')],
                                        [0, '', ''],
                                        [1, 'foo', ('str', 'bar')],
                                        [0, 'beta', ('str', 'hello world')]
                                    ],
                                    'description': None
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
                                    'passed': True,
                                    'description':
                                        'match with regex & custom func',
                                },
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
                            ]
                        ),
                    ]
                )
            ]
        ),
    ]
)
