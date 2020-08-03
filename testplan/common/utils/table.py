"""Utilities for working with tables."""
import six
import collections


def all_are(objs, *are_what):
    # type: (Iterable[Any], Type) -> bool
    return all(isinstance(obj, are_what) for obj in objs)


class TableEntry(object):
    """
    Represents a table. Internally represented either
    as a ``list`` of ``list`` or a ``list`` of ``dict``.
    """

    def __init__(self, table):
        self.table = self._validate_table(table or [])

    @staticmethod
    def _validate_table(table):
        if isinstance(table, (list, tuple)):
            if all_are(table, dict) or all_are(table, list, tuple):
                return table
        raise TypeError((
            "`table` must be a list of"
            " lists or list of dicts, got:\n{}".format(table)
        ))

    def __len__(self):
        if not self.table:
            return 0
        elif isinstance(self.table[0], list):
            return len(self.table) - 1
        return len(self.table)

    @property
    def column_names(self):
        """
        Returns the column names of the table

        :return: the column names
        :rtype: ``list`` of ``str``
        """
        if isinstance(self.table[0], dict):
            return self.table[0].keys()
        else:
            assert isinstance(self.table[0], list)
            return self.table[0]

    @staticmethod
    def consolidate_columns(list_of_dict, placeholder="ABSENT"):
        """
        In some cases the raw DB results may return a
        list of dictionaries that have different keys.

        This method allows us to have the same keys for each row,
        which would then be compatible with logging & matching logic.

        :return: table rows with same keys,
            missing ones replaced with ``placeholder``
        :rtype: ``list`` of ``dict``
        """
        columns = set()

        for row in list_of_dict:
            columns = columns.union(row.keys())

        return [
            {col: row.get(col, placeholder) for col in columns}
            for row in list_of_dict
        ]

    def as_list_of_list(self):
        """
        Returns the table as ``list`` of ``list``

        :return: the table
        :rtype: ``list`` of ``list`` for the table

        """
        table = self.table
        formatted_table = []

        # if ``list`` of ``dict``, then we convert to ``list`` of ``list``
        # with dict elements indexed by column_names

        if isinstance(table[0], dict):
            keys = table[0].keys()
            formatted_table.append(keys)
            for row in table:
                formatted_table.append([row[k] for k in keys])
        else:
            # else it must be ``list`` of ``list``
            assert isinstance(table[0], list)
            formatted_table = table

        return formatted_table

    def as_list_of_dict(self, keep_column_order=False):
        """
        Returns the table as ``list`` of ``dict``

        :return: the table
        :rtype: ``list`` of ``dict`` for the table
        """
        table = self.table
        formatted_table = []

        # if ``list`` of ``list``, then we convert to ``list`` of ``dict``
        # with dict elements indexed by column_names
        if isinstance(table[0], (list, tuple)):
            column_names = table[0]
            for row in table[1:]:
                tups = [
                    (column, row[col_idx])
                    for col_idx, column in enumerate(column_names)
                ]
                if keep_column_order:
                    formatted_table.append(collections.OrderedDict(tups))
                else:
                    formatted_table.append(dict(tups))
        else:
            # else it must be ``list`` of ``dict``
            assert isinstance(table[0], dict)
            formatted_table = table

        return formatted_table
