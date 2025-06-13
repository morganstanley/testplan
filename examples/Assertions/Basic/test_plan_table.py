#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of table assertion namespaces.
"""

import re
import sys
import random
from copy import deepcopy

from testplan import test_plan
from testplan.common.utils import comparison
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.serialization.fields import LogLink, FormattedValue
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class TableSuite:
    """
    We can use `result.table` namespace to apply table specific checks.
    A table is represented either as a
    list of dictionaries, or a list of lists
    that have columns as the first item and the
    rows as the rest
    """

    @testcase
    def test_table_namespace(self, env, result):
        list_of_dicts = [
            {"name": "Bob", "age": 32},
            {"name": "Susan", "age": 24},
            {"name": "Rick", "age": 67},
        ]

        list_of_lists = [
            ["name", "age"],
            ["Bob", 32],
            ["Susan", 24],
            ["Rick", 67],
        ]

        tuple_of_tuples = tuple(tuple(r) for r in list_of_lists)

        sample_table = [
            ["symbol", "amount"],
            ["AAPL", 12],
            ["GOOG", 21],
            ["FB", 32],
            ["AMZN", 5],
            ["MSFT", 42],
        ]

        large_table = [sample_table[0]] + sample_table[1:] * 100

        # We can log the table using result.table.log, either a list of dicts
        # or a list of lists

        result.table.log(list_of_dicts, description="Table Log: list of dicts")
        result.table.log(
            list_of_lists,
            display_index=True,
            description="Table Log: list of lists",
        )
        result.table.log(
            tuple_of_tuples, description="Table Log: tuple of tuples"
        )
        result.table.log(list_of_lists[:1], description="Empty table")
        result.table.log(
            [{"name": "Bob", "age": 32}, {"name": "Susan"}],
            description="Empty cell",
        )
        result.table.log(
            [[1, 2, 3], ["abc", "def", "xyz"]], description="Non-string header"
        )

        # When tables with over 10 rows are logged:
        #   * In the PDF report, only the first and last 5 rows are shown. The
        #     row indices are then also shown by default.
        #   * In console out the entire table will be shown, without indices.
        result.table.log(large_table[:21], description="Table Log: many rows")

        # When tables are too wide:
        #   * In the PDF report, the columns are split into tables over multiple
        #     rows. The row indices are then also shown by default.
        #   * In console out the table will be shown as is, if the formatting
        #     looks odd the output can be piped into a file.
        columns = [["col_{}".format(i) for i in range(20)]]
        rows = [
            ["row {} col {}".format(i, j) for j in range(20)]
            for i in range(10)
        ]
        result.table.log(columns + rows, description="Table Log: many columns")

        # When the cell values exceed the character limit:
        #   * In the PDF report they will be truncated and appended with '...'.
        #   * In console out, should they also be truncated?
        long_cell_table = [
            ["Name", "Age", "Address"],
            ["Bob Stevens", "33", "89 Trinsdale Avenue, LONDON, E8 0XW"],
            ["Susan Evans", "21", "100 Loop Road, SWANSEA, U8 12JK"],
            ["Trevor Dune", "88", "28 Kings Lane, MANCHESTER, MT16 2YT"],
            ["Belinda Baggins", "38", "31 Prospect Hill, DOYNTON, BS30 9DN"],
            ["Cosimo Hornblower", "89", "65 Prospect Hill, SURREY, PH33 4TY"],
            ["Sabine Wurfel", "31", "88 Clasper Way, HEXWORTHY, PL20 4BG"],
        ]
        result.table.log(long_cell_table, description="Table Log: long cells")

        # Add external/internal link in the table log
        result.table.log(
            [
                ["Description", "Data"],
                [
                    "External Link",
                    LogLink(link="https://www.google.com", title="Google"),
                ],
                # Require plan.runnable.disable_reset_report_uid() in main function
                # to avoid generating uuid4 as the report uid so that we can use
                # the test name as the link in the report.
                [
                    "Internal Link",
                    LogLink(
                        link="/Assertions%20Test/SampleSuite/test_basic_assertions",
                        title="test_basic_assertions",
                        inner=True,
                    ),
                ],
            ],
            description="Link to external/internal",
        )

        # Customize formatted value in the table log
        result.table.log(
            [
                ["Description", "Data"],
                [
                    "Formatted Value - 0.6",
                    FormattedValue(display="60%", value=0.6),
                ],
                [
                    "Formatted Value - 0.08",
                    FormattedValue(display="8%", value=0.08),
                ],
            ],
            description="Formatted value",
        )

        result.table.match(
            list_of_lists,
            list_of_lists,
            description="Table Match: list of list vs list of list",
        )

        result.table.match(
            list_of_dicts,
            list_of_dicts,
            description="Table Match: list of dict vs list of dict",
        )

        result.table.match(
            list_of_dicts,
            list_of_lists,
            description="Table Match: list of dict vs list of list",
        )

        result.table.diff(
            list_of_lists,
            list_of_lists,
            description="Table Diff: list of list vs list of list",
        )

        result.table.diff(
            list_of_dicts,
            list_of_dicts,
            description="Table Diff: list of dict vs list of dict",
        )

        result.table.diff(
            list_of_dicts,
            list_of_lists,
            description="Table Diff: list of dict vs list of list",
        )

        # For table match, Testplan allows use of custom comparators
        # (callables & regex) instead of plain value matching

        actual_table = [
            ["name", "age"],
            ["Bob", 32],
            ["Susan", 24],
            ["Rick", 67],
        ]

        expected_table = [
            ["name", "age"],
            # Regex match for row 1, name column
            # Callable match for row 1, age column
            [re.compile(r"\w{3}"), lambda age: 30 < age < 40],
            ["Susan", 24],  # simple match with exact values for row 2
            # Callable match for row 3 name column
            # Simple match for row 3 age column
            [lambda name: name in ["David", "Helen", "Pablo"], 67],
        ]

        result.table.match(
            actual_table,
            expected_table,
            description="Table Match: simple comparators",
        )

        result.table.diff(
            actual_table,
            expected_table,
            description="Table Diff: simple comparators",
        )

        # Equivalent assertion as above, using Testplan's custom comparators
        # These utilities produce more readable output

        expected_table_2 = [
            ["name", "age"],
            [
                re.compile(r"\w{3}"),
                comparison.Greater(30) & comparison.Less(40),
            ],
            ["Susan", 24],
            [comparison.In(["David", "Helen", "Pablo"]), 67],
        ]

        result.table.match(
            actual_table,
            expected_table_2,
            description="Table Match: readable comparators",
        )

        result.table.diff(
            actual_table,
            expected_table_2,
            description="Table Diff: readable comparators",
        )

        # By default `None` value means the cell is empty, it is
        # used as a placeholder

        table = [
            ["Action", "Col1", "Col2", "Col3"],
            ["Action1", "Value1", "Value2", None],
            ["Action2", "Value1", None, "Value3"],
            ["Action3", None, "Value2", "Value3"],
        ]
        expected_table = [
            ["Action", "Col1", "Col2"],
            ["Action1", "Value1", "Value2"],
            ["Action2", "Value1", None],
            ["Action3", None, "Value2"],
        ]
        result.table.match(
            table,
            expected_table,
            description="Table Match: Empty cells",
            include_columns=["Action", "Col1", "Col2"],
        )
        result.table.diff(
            table,
            expected_table,
            description="Table Diff: Empty cells",
            exclude_columns=["Col3"],
        )

        # The match and diff can be limited to certain columns

        table = self.create_table(3, 5)
        mod_table = deepcopy(table)
        mod_table[0]["column_0"] = 123
        mod_table[1]["column_1"] = 123

        result.table.match(
            table,
            mod_table,
            include_columns=["column_1", "column_2"],
            report_all=True,
            description="Table Match: Ignored columns",
        )

        table = self.create_table(3, 5)
        mod_table = deepcopy(table)
        mod_table[0]["column_0"] = 123
        mod_table[1]["column_1"] = 123

        result.table.diff(
            table,
            mod_table,
            include_columns=["column_1", "column_2"],
            report_all=True,
            description="Table Diff: Ignored columns",
        )

        # While comparing tables with large number of columns
        # we can 'trim' some of the columns to get more readable output

        table_with_many_columns = self.create_table(30, 10)

        # Only use 2 columns for comparison, trim the rest
        result.table.match(
            table_with_many_columns,
            table_with_many_columns,
            include_columns=["column_1", "column_2"],
            report_all=False,
            description="Table Match: Trimmed columns",
        )

        result.table.diff(
            table_with_many_columns,
            table_with_many_columns,
            include_columns=["column_1", "column_2"],
            report_all=False,
            description="Table Diff: Trimmed columns",
        )

        # While comparing tables with large number of rows
        # we can stop comparing if the number of failed rows exceeds the limit

        matching_rows_1 = [
            {"amount": idx * 10, "product_id": random.randint(1000, 5000)}
            for idx in range(5)
        ]

        matching_rows_2 = [
            {"amount": idx * 10, "product_id": random.randint(1000, 5000)}
            for idx in range(500)
        ]

        row_diff_a = [
            {"amount": 25, "product_id": 1111},
            {"amount": 20, "product_id": 2222},
            {"amount": 50, "product_id": 3333},
        ]

        row_diff_b = [
            {"amount": 35, "product_id": 1111},
            {"amount": 20, "product_id": 1234},
            {"amount": 20, "product_id": 5432},
        ]

        table_a = matching_rows_1 + row_diff_a + matching_rows_2
        table_b = matching_rows_1 + row_diff_b + matching_rows_2

        # We can 'trim' some rows and display at most 2 rows of failures
        result.table.match(
            table_a,
            table_b,
            fail_limit=2,
            report_all=False,
            description="Table Match: Trimmed rows",
        )

        # Only display mismatching rows, with a maximum limit of 2 rows
        result.table.diff(
            table_a,
            table_b,
            fail_limit=2,
            report_all=False,
            description="Table Diff: Trimmed rows",
        )

        # result.table.column_contain can be used for checking if all of the
        # cells on a table's column exists in a given list of values
        result.table.column_contain(
            values=["AAPL", "AMZN"], table=sample_table, column="symbol"
        )

        # We can use `limit` and `report_fails_only` arguments for producing
        # less output for large tables

        result.table.column_contain(
            values=["AAPL", "AMZN"],
            table=large_table,
            column="symbol",
            limit=20,  # Process 50 items at most
            report_fails_only=True,  # Only include failures in the result
        )

    @staticmethod
    def create_table(num_cols, num_rows):
        return [
            {"column_{}".format(idx): i * idx for idx in range(num_cols)}
            for i in range(num_rows)
        ]


@test_plan(
    name="Table Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    # For saving the internal link in the report, use test
    # name instead of uuid4 as report uid.
    plan.runnable.disable_reset_report_uid()

    plan.add(
        MultiTest(
            name="Table Assertions Test",
            suites=[
                TableSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
