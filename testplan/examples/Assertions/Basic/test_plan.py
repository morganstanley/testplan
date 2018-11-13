#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of assertions,
assertion groups and assertion namespaces.
"""
import os
import random
import re
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.common.utils import comparison
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SampleSuite(object):

    @testcase
    def test_basic_assertions(self, env, result):
        # Basic assertions contain equality, comparison, membership checks:
        result.equal('foo', 'foo')  # The most basic syntax

        # We can pass description to any assertion method
        result.equal(1, 2, 'Description for failing equality')

        result.not_equal('foo', 'bar')
        result.greater(5, 2)
        result.greater_equal(2, 2)
        result.greater_equal(2, 1)
        result.less(10, 20)
        result.less_equal(10, 10)
        result.less_equal(10, 30)

        # We can access these assertions via shortcuts as well,
        # They will have the same names with the functions
        # in the built-in `operator` module
        result.eq(15, 15)
        result.ne(10, 20)
        result.lt(2, 3)
        result.gt(3, 2)
        result.le(10, 15)
        result.ge(15, 10)

        # We can test if 2 numbers are close to each other within
        # the relative tolerance or a minimum absolute tolerance level
        result.isclose(100, 95, 0.1, 0.0)
        result.isclose(100, 95, 0.01, 0.0)

        # `result` also has a `log` method that can be used
        # for adding extra information on the output
        result.log(
            'This is a log message, it will be displayed'
            ' along with other assertion details.'
        )

        # Boolean checks
        result.true('foo' == 'foo', description='Boolean Truthiness check')
        result.false(5 < 2, description='Boolean Falseness check')

        result.fail('This is an explicit failure.')

        # Membership checks
        result.contain('foo', 'foobar', description='Passing membership')
        result.not_contain(
            member=10,
            container={'a': 1, 'b': 2},
            description='Failing membership'
        )

        # Slice comparison (inclusion)
        result.equal_slices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            ['a', 'b', 3, 4, 'c', 'd', 7, 8],
            slices=[slice(2, 4), slice(6, 8)],
            description='Comparison of slices'
        )

        # Slice comparison (exclusion)
        # For the example below, each separate slice comparison fails
        # however the overall assertion still passes as common exclusion
        # indices of two slices are [2, 3], which is the same values `3`, `4`
        # in both iterables.
        result.equal_exclude_slices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            ['a', 'b', 3, 4, 'c', 'd', 'e', 'f'],
            slices=[slice(0, 2), slice(4, 8)],
            description='Comparison of slices (exclusion)'
        )

        # We can test if 2 blocks of textual content have differences with
        # comparison option --ignore-space-change, --ignore-whitespaces and
        # --ignore-blank-lines, also we can spefify output delta in unified
        # or context mode.
        result.diff('abc\nxyz\n', 'abc\nxyz\n\n', ignore_blank_lines=True)
        result.diff(
            '1\r\n1\r\n1\r\nabc\r\nxy z\r\n2\r\n2\r\n2\r\n',
            '1\n1\n1\nabc \nxy\t\tz\n2\n2\n2\n',
            ignore_space_change=True, unified=3
        )

    @testcase
    def test_raised_exceptions(self, env, result):
        # `result` object has `raises` and `not_raises` methods that can be
        # as context managers to check if a given block of code raises / not
        # raises a given exception:

        with result.raises(KeyError):
            {'foo': 3}['bar']

        # Exception message pattern check (`re.search` is used implicitly)

        with result.raises(
            ValueError,
            pattern='foobar',
            description='Exception raised with custom pattern.'
        ):
            raise ValueError('abc foobar xyz')

        # Custom function check (func should accept
        # exception object as a single arg)

        class MyException(Exception):

            def __init__(self, value):
                self.value = value

        def custom_func(exc):
            return exc.value % 2 == 0

        with result.raises(
            MyException,
            func=custom_func,
            description='Exception raised with custom func.'
        ):
            raise MyException(4)

        # `not_raises` passes when raised exception
        # type does match any of the declared exception classes
        # It is logically inverse of `result.raises`.

        with result.not_raises(TypeError):
            {'foo': 3}['bar']

        # `not_raises` can also check if a certain exception has been raised
        # WITHOUT matching the given `pattern` or `func`

        # Exception type matches but pattern does not -> Pass
        with result.not_raises(
            ValueError,
            pattern='foobar',
            description='Exception not raised with custom pattern.'
        ):
            raise ValueError('abc')

        # Exception type matches but func does not -> Pass
        with result.not_raises(
            MyException,
            func=custom_func,
            description='Exception not raised with custom func.'
        ):
            raise MyException(5)

    @testcase
    def test_assertion_group(self, env, result):
        # result object has a `group` method that can be used for grouping
        # assertions together. This has no effect on stdout, however it will
        # be formatted with extra indentation on PDF reports for example.

        result.equal(1, 1, description='Equality assertion outside the group')

        with result.group(description='Custom group description') as group:
            group.not_equal(2, 3, description='Assertion within a group')
            group.greater(5, 3)

            # Groups can have sub groups as well:
            with group.group(description='This is a sub group') as sub_group:
                sub_group.less(6, 3, description='Assertion within sub group')

        result.equal(
            'foo', 'foo', description='Final assertion outside all groups')

    # `result` object has namespaces that contain specialized
    # methods for more advanced assertions

    @testcase
    def test_regex_namespace(self, env, result):
        # `result.regex` contains methods for regular expression assertions

        # `regex.match` applies `re.match` with the given `regexp` and `value`
        result.regex.match(
            regexp='foo',
            value='foobar', description='string pattern match')

        # We can also pass compiled SRE objects as well:
        result.regex.match(
            regexp=re.compile('foo'),
            value='foobar', description='SRE match')

        # `regex.multiline_match` implicitly passes `re.MULTILINE`
        # and `re.DOTALL` flags to `re.match`

        multiline_text = os.linesep.join([
            'first line',
            'second line',
            'third line'
        ])

        result.regex.multiline_match('first line.*second', multiline_text)

        # `regex.not_match` returns True if the
        # given pattern does not match the value

        result.regex.not_match('baz', 'foobar')

        # `regex.multiline_not_match` implicitly passes `re.MULTILINE`
        # and `re.DOTALL` flags to `re.match`

        result.regex.multiline_not_match('foobar', multiline_text)

        # `regex.search` runs pattern match via `re.search`
        result.regex.search('second', multiline_text)

        # `regex.search_empty` returns True when the given
        # pattern does not exist in the text.
        result.regex.search_empty(
            'foobar', multiline_text, description='Passing search empty')

        result.regex.search_empty(
            'second', multiline_text, description='Failing search_empty')

        # `regex.findall` matches all of the occurrences of the pattern
        # in the given string and optionally runs an extra condition function
        # against the number of matches
        text = 'foo foo foo bar bar foo bar'

        result.regex.findall(
            regexp='foo',
            value=text,
            condition=lambda num_matches: 2 < num_matches < 5
        )

        # Equivalent assertion with more readable output
        result.regex.findall(
            regexp='foo',
            value=text,
            condition=comparison.Greater(2) & comparison.Less(5)
        )

        # `regex.matchline` can be used for checking if a given pattern
        # matches one or more lines in the given text
        result.regex.matchline(
            regexp=re.compile(r'\w+ line$'),
            value=multiline_text,
        )


    @testcase
    def test_table_namespace(self, env, result):
        # We can use `result.table` namespace to apply table specific checks.
        # 1- A table is represented either as a
        # list of dictionaries with uniform keys (columns)
        # 2- Or a list of lists that have columns as the first item and the
        # row values as the rest

        list_of_dicts = [
            {'name': 'Bob', 'age': 32},
            {'name': 'Susan', 'age': 24},
            {'name': 'Rick', 'age': 67},
        ]

        list_of_lists = [
            ['name', 'age'],
            ['Bob', 32],
            ['Susan', 24],
            ['Rick', 67]
        ]

        result.table.match(
            list_of_lists, list_of_lists,
            description='Table Match: list of list vs list of list'
        )

        result.table.match(
            list_of_dicts, list_of_dicts,
            description='Table Match: list of dict vs list of dict'
        )

        result.table.match(
            list_of_dicts, list_of_lists,
            description='Table Match: list of dict vs list of list'
        )

        # For table match, Testplan allows use of custom comparators
        # (callables & regex) instead of plain value matching

        actual_table = [
            ['name', 'age'],
            ['Bob', 32],
            ['Susan', 24],
            ['Rick', 67]
        ]

        expected_table = [
            ['name', 'age'],
            # Regex match for row 1, name column
            # Callable match for row 1, age column
            [re.compile(r'\w{3}'), lambda age: 30 < age < 40],
            ['Susan', 24],  # simple match with exact values for row 2
            # Callable match for row 3 name column
            # Simple match for row 3 age column
            [
                lambda name: name in ['David', 'Helen', 'Pablo'],
                67,
            ]
        ]

        result.table.match(
            actual_table, expected_table,
            description='Table Match: simple comparators'
        )

        # Equivalent assertion as above, using Testplan's custom comparators
        # These utilities produce more readable output
        expected_table_2 = [
            ['name', 'age'],
            [
                re.compile(r'\w{3}'),
                comparison.Greater(30) & comparison.Less(40)
            ],
            ['Susan', 24],
            [comparison.In(['David', 'Helen', 'Pablo']), 67]
        ]

        result.table.match(
            actual_table, expected_table_2,
            description='Table Match: readable comparators'
        )

        # While comparing tables with large number of columns
        # we can 'trim' some of the columns to get more readable output

        table_with_many_columns = [
            {'column_{}'.format(idx): i * idx for idx in range(30)}
            for i in range(10)
        ]

        # Only use 2 columns for comparison, trim the rest
        result.table.match(
            table_with_many_columns,
            table_with_many_columns,
            include_columns=['column_1', 'column_2'],
            report_all=False,
            description='Table Match: Trimmed columns'
        )

        # While comparing tables with large number of rows
        # we can 'trim' some rows and display a limited number of failures only

        matching_rows = [
            {'amount': idx * 10, 'product_id': random.randint(1000, 5000)}
            for idx in range(500)
        ]

        row_diff_a = [
            {'amount': 25, 'product_id': 1111},
            {'amount': 20, 'product_id': 2222},
            {'amount': 50, 'product_id': 3333},
        ]

        row_diff_b = [
            {'amount': 35, 'product_id': 1111},
            {'amount': 20, 'product_id': 1234},
            {'amount': 20, 'product_id': 5432},
        ]

        table_a = matching_rows + row_diff_a + matching_rows
        table_b = matching_rows + row_diff_b + matching_rows

        # Only display mismatching rows, with a maximum limit of 2 rows
        result.table.match(
            table_a,
            table_b,
            fail_limit=2,
            report_all=False,
            description='Table Match: Trimmed rows'
        )

        # result.table.column_contain can be used for checking if all of the
        # cells on a table's column exists in a given list of values
        sample_table = [
            ['symbol', 'amount'],
            ['AAPL', 12],
            ['GOOG', 21],
            ['FB', 32],
            ['AMZN', 5],
            ['MSFT', 42]
        ]

        result.table.column_contain(
            values=['AAPL', 'AMZN'],
            table=sample_table,
            column='symbol',
        )

        # We can use `limit` and `report_fails_only` arguments for producing
        # less output for large tables

        large_table = [sample_table[0]] + sample_table[1:] * 100

        result.table.column_contain(
            values=['AAPL', 'AMZN'],
            table=large_table,
            column='symbol',
            limit=20,  # Process 50 items at most
            report_fails_only=True,  # Only include failures in the result
        )

        # We can log the table using result.table.log, either a list of dicts
        # or a list of lists
        result.table.log(list_of_dicts, description='Table Log: list of dicts')
        result.table.log(list_of_lists, description='Table Log: list of lists')

        # When tables with over 10 rows are logged:
        #   * In the PDF report, only the first and last 5 rows are shown. The
        #     row indices are then also shown by default.
        #   * In console out the entire table will be shown, without indices.
        result.table.log(large_table[:21], description='Table Log: many rows')

        # When tables are too wide:
        #   * In the PDF report, the columns are split into tables over multiple
        #     rows. The row indices are then also shown by default.
        #   * In console out the table will be shown as is, if the formatting
        #     looks odd the output can be piped into a file.
        columns = [['col_{}'.format(i) for i in range(20)]]
        rows = [['row {} col {}'.format(i, j)
                 for j in range(20)]
                for i in range(10)]
        result.table.log(columns + rows, description='Table Log: many columns')

        # When the cell values exceed the character limit:
        #   * In the PDF report they will be truncated and appended with '...'.
        #   * In console out, should they also be truncated?
        long_cell_table = [
            ['Name', 'Age', 'Address'],
            ['Bob Stevens', '33', '89 Trinsdale Avenue, LONDON, E8 0XW'],
            ['Susan Evans', '21', '100 Loop Road, SWANSEA, U8 12JK'],
            ['Trevor Dune', '88', '28 Kings Lane, MANCHESTER, MT16 2YT'],
            ['Belinda Baggins', '38', '31 Prospect Hill, DOYNTON, BS30 9DN'],
            ['Cosimo Hornblower', '89', '65 Prospect Hill, SURREY, PH33 4TY'],
            ['Sabine Wurfel', '31', '88 Clasper Way, HEXWORTHY, PL20 4BG'],
        ]
        result.table.log(long_cell_table, description='Table Log: long cells')


    @testcase
    def test_dict_namespace(self, env, result):
        # `result.dict` namespace can be used for applying advanced
        # assertion rules to dictionaries, which can be nested.

        actual = {
            'foo': 1,
            'bar': 2,
        }

        expected = {
            'foo': 1,
            'bar': 5,
            'extra-key': 10,
        }

        # `dict.match` (recursively) matches elements of the dictionaries
        result.dict.match(actual, expected, description='Simple dict match')

        # `dict.match` supports nested data as well

        actual = {
            'foo': {
                'alpha': [1, 2, 3],
                'beta': {'color': 'red'}
            }
        }

        expected = {
            'foo': {
                'alpha': [1, 2],
                'beta': {'color': 'blue'}
            }
        }

        result.dict.match(actual, expected, description='Nested dict match')

        # It is possible to use custom comparators with `dict.match`
        actual = {
            'foo': [1, 2, 3],
            'bar': {'color': 'blue'},
            'baz': 'hello world',
        }

        expected = {
            'foo': [1, 2, lambda v: isinstance(v, int)],
            'bar': {
                'color': comparison.In(['blue', 'red', 'yellow'])
            },
            'baz': re.compile(r'\w+ world'),
        }

        result.dict.match(
            actual, expected, description='Dict match: Custom comparators')

        # `dict.check` can be used for checking existence / absence
        # of keys within a dictionary

        result.dict.check(
            dictionary={
                'foo': 1, 'bar': 2, 'baz': 3,
            },
            has_keys=['foo', 'alpha'],
            absent_keys=['bar', 'beta']
        )

        # `dict.log` can be used to log a dictionary in human readable format.

        result.dict.log(
            dictionary={
                'foo': [1, 2, 3],
                'bar': {'color': 'blue'},
                'baz': 'hello world',
            }
        )

    @testcase
    def test_fix_namespace(self, env, result):
        # `result.fix` namespace can be used for applying advanced
        # assertion rules to fix messages, which can
        # be nested (e.g. repeating groups)
        # For more info about FIX protocol, please see:
        # https://en.wikipedia.org/wiki/Financial_Information_eXchange

        # `fix.match` can compare two fix messages, and
        # supports custom comparators (like `dict.match`)

        fix_msg_1 = {
            36: 6,
            22: 5,
            55: 2,
            38: 5,
            555: [
                {
                    600: 'A',
                    601: 'A',
                    683: [
                        {
                            688: 'a',
                            689: 'a'
                        },
                        {
                            688: 'b',
                            689: 'b'
                        }
                    ]
                },
                {
                    600: 'B',
                    601: 'B',
                    683: [
                        {
                            688: 'c',
                            689: 'c'
                        },
                        {
                            688: 'd',
                            689: 'd'
                        }
                    ]
                }
            ]
        }

        fix_msg_2 = {
            36: 6,
            22: 5,
            55: 2,
            38: comparison.GreaterEqual(4),
            555: [
                {
                    600: 'A',
                    601: 'B',
                    683: [
                        {
                            688: 'a',
                            689: re.compile(r'[a-z]')
                        },
                        {
                            688: 'b',
                            689: 'b'
                        }
                    ]
                },
                {
                    600: 'C',
                    601: 'B',
                    683: [
                        {
                            688: 'c',
                            689: comparison.In(('c', 'd'))
                        },
                        {
                            688: 'd',
                            689: 'd'
                        }
                    ]
                }
            ]
        }
        result.fix.match(fix_msg_1, fix_msg_2)

        # `fix.check` can be used for checking existence / absence
        # of certain tags in a fix message

        result.fix.check(
            msg=fix_msg_1,
            has_tags=[26, 22, 11],
            absent_tags=[444, 555],
        )

        # `fix.log` can be used to log a fix message in human readable format.

        result.fix.log(
            msg={
                36: 6,
                22: 5,
                55: 2,
                38: 5,
                555:[
                    {556: 'USD', 624: 1},
                    {556: 'EUR', 624: 2}
                ]
            }
        )

    @testcase
    def test_xml_namespace(self, env, result):
        # `result.xml` namespace can be used for applying advanced assertion
        # logic onto XML data.

        # `xml.check` can be used for checking if given tags & XML namespaces
        # contain the expected values

        xml_1 = '''
            <Root>
                <Test>Foo</Test>
            </Root>
        '''

        result.xml.check(
            element=xml_1,
            xpath='/Root/Test',
            description='Simple XML check for existence of xpath.'
        )

        xml_2 = '''
            <Root>
                <Test>Value1</Test>
                <Test>Value2</Test>
            </Root>
        '''

        result.xml.check(
            element=xml_2,
            xpath='/Root/Test',
            tags=['Value1', 'Value2'],
            description='XML check for tags in the given xpath.'
        )

        xml_3 = '''
            <SOAP-ENV:Envelope
              xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                <SOAP-ENV:Header/>
                <SOAP-ENV:Body>
                    <ns0:message
                      xmlns:ns0="http://testplan">Hello world!</ns0:message>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>
        '''

        result.xml.check(
            element=xml_3,
            xpath='//*/a:message',
            tags=[re.compile(r'Hello*')],
            namespaces={"a": "http://testplan"},
            description='XML check with namespace matching.'
        )


@test_plan(
    name='Assertions Example',
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL,
        failing=StyleEnum.ASSERTION_DETAIL
    )
)
def main(plan):
    plan.add(MultiTest(name='Assertions Test', suites=[SampleSuite()]))


if __name__ == '__main__':
    sys.exit(not main())
