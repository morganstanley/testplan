"""Small wrapper driver around sqlite3 library."""

import os
import sqlite3
import functools

from contextlib import contextmanager

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized

from .base import Driver, DriverConfig


class Sqlite3Config(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.sqlite.Sqlite3` resource.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.

        """
        return {
            "db_path": str,
            ConfigOption("connect_at_start", default=True): bool,
        }


def _rollback_on_error(func):
    """Rollback the databse if db operation raises."""

    @functools.wraps(func)
    def wrap(self, *args):
        try:
            return func(self, *args)
        except Exception as exc:
            self.logger.error(
                "Exception while executing: %s%s%s", args, os.sep, exc
            )
            self.db.rollback()
            raise

    return wrap


class Sqlite3(Driver):
    """
    Basic sqlite3 driver to add to a MultiTest environment, connect to
    a database and perform sql queries etc.

    {emphasized_members_docs}

    :param db_path: Path to the database file to connect to. In case a relative
        path is provided it will be appended to the runpath.
    :type db_path: ``str``
    :param connect_at_start: Connect to the database when driver starts.
      Default: True
    :type connect_at_start: ``bool``
    """

    CONFIG = Sqlite3Config

    def __init__(
        self, name: str, db_path: str, connect_at_start: bool = True, **options
    ):
        options.update(self.filter_locals(locals()))
        super(Sqlite3, self).__init__(**options)
        self.db = None
        self.cursor = None

    @emphasized
    @property
    def db_path(self):
        """Database file path."""
        # if self.cfg.db_path is an absolute path it will return self.cfg.db_path
        return os.path.join(self.runpath, self.cfg.db_path)

    def connect(self):
        """Connect to the database and set the internal db cursor."""
        self.db = sqlite3.connect(self.db_path)
        self.cursor = self.db.cursor()

    def starting(self):
        """
        Start the driver.
        """
        super(Sqlite3, self).starting()
        if self.cfg.connect_at_start:
            self.connect()

    def stopping(self):
        """
        Stop the driver.
        """
        super(Sqlite3, self).stopping()
        if self.db:
            self.db.close()

    def aborting(self, *args, **kwargs):
        """
        Abort the driver.
        """
        if self.db:
            self.db.close()

    @contextmanager
    def commit_at_exit(self):
        """
        Context manager to perform operations and .commit() at exit.
        """
        yield
        self.db.commit()

    def commit(self):
        """Commit db changes."""
        self.db.commit()

    @_rollback_on_error
    def execute(self, *args, **kwargs):
        """Invoke cursor execute."""
        self.cursor.execute(*args, **kwargs)

    @_rollback_on_error
    def executemany(self, *args):
        """Invoke cursor executemany."""
        self.cursor.executemany(*args)

    def fetchone(self):
        """Invoke cursor fetchone."""
        return self.cursor.fetchone()

    def fetchall(self):
        """Invoke cursor fetchall."""
        return self.cursor.fetchall()

    def fetch_table(self, table, columns=None):
        """
        Fetch a table from the db. The first row will be the column names
        and the following rows will be the table rows. Returns a table like:

        .. code-block:: bash

            [
              ['symbol', 'amount'],
              ['AAPL', 12],
              ['GOOG', 21],
              ['FB', 32],
              ['AMZN', 5],
              ['MSFT', 42]
            ]

        :param table: Table name in the db.
        :type table: ``str``
        :param columns: Names of columns to be fetched.
        :type columns: ``list`` of ``str``
        :return: The table contents.
        :rtype: ``list`` of ``list`` of values.
        """
        if columns is None:
            self.execute("PRAGMA table_info({})".format(table))
            columns = [str(col[1]) for col in self.cursor.fetchall()]

        self.execute("SELECT {} FROM {}".format(", ".join(columns), table))

        table = [columns]
        for row in self.cursor.fetchall():
            table.append([item for item in row])
        return table
