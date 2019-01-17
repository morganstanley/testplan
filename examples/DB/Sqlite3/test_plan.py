#!/usr/bin/env python
"""
Demostrates Sqlite3 driver usage from within the testcases.
"""

import sys

from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.sqlite import Sqlite3

from testplan import test_plan
from testplan.testing.multitest import testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


@testsuite
class DBQueries(object):
    """Suite that contains testcases that perform db queries."""

    def setup(self, env, result):
        """
        Setup method that will be executed before all testcases. It is
        used to create the tables that the testcases require.
        """
        # Create a table called 'users'.
        with env.db.commit_at_exit():
            env.db.execute('''DROP TABLE IF EXISTS users''')
            env.db.execute(
                '''CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT,
                           phone TEXT, email TEXT unique, password TEXT)''')

        # Fill the table with data.
        with env.db.commit_at_exit():
            items = [{'name': 'John', 'phone': '123456',
                      'email': 'john@email', 'password': 'abc123'},
                     {'name': 'Mary', 'phone': '234567',
                      'email': 'mary@email', 'password': 'qwe234'}]
            env.db.executemany(
                '''INSERT INTO users(name, phone, email, password)
                  VALUES(:name,:phone, :email, :password)''', items)
        result.log('Database file "{}" of driver "{}" created at "{}"'.format(
            env.db.cfg.db_name, env.db.cfg.name, env.db.db_path))

    @testcase
    def sample_match_query(self, env, result):
        """Table match example after fetching two table columns."""
        table = env.db.fetch_table('users', columns=['name', 'email'])
        result.table.log(table, description='Two columns.')

        expected_table = [
            ['name', 'email'],
            ['John', 'john@email'],
            ['Mary', 'mary@email']
        ]

        # Match the table fetched against the expected.
        result.table.match(
            actual=table,
            expected=expected_table
        )

    @testcase
    def sample_column_query(self, env, result):
        """Table column content assertion after fetching the whole table."""
        table = env.db.fetch_table('users')
        result.table.log(table, description='Whole table.')

        # Checks that the column 'name' of the table contain one of the
        # expected values.
        result.table.column_contain(
            values=['John', 'Mary'],
            table=env.db.fetch_table('users'),
            column='name',
        )

    def teardown(self, env):
        env.db.execute('DROP TABLE IF EXISTS users')


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name='Sqlite3Example',
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    pdf_path='report.pdf'
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    plan.add(MultiTest(name='Sqlite3Test',
                       suites=[DBQueries()],
                       environment=[
                           Sqlite3(name='db',
                                   db_name='mydb')]))


if __name__ == '__main__':
    sys.exit(not main())
