"""Utilities for working with tables."""
import six
import collections


class TableEntry(object):
    """
    Represents a table. Internally represented either
    as a ``list`` of ``list`` or a ``list`` of ``dict``.
    """

    def __init__(self, table):
        table = table or []
        self._check_table(table)
        self.table = table

    def _check_table(self, table):
        """Make the original table argument is a valid."""
        error_msg = '`table` must be a list of' \
                    ' lists or list of dicts: {}'.format(table)

        if not isinstance(table, (list, tuple)):
            raise ValueError(error_msg)

        is_list_of_list = all(isinstance(obj, (list, tuple)) for obj in table)
        is_list_of_dict = all(isinstance(obj, dict) for obj in table)

        if not (is_list_of_dict or is_list_of_list) and table:
            raise ValueError(error_msg)

        if is_list_of_list and table and not all(
                isinstance(col, six.string_types) for col in table[0]):
            raise ValueError(
                'For list of lists, first element must'
                ' be the list column names: {}'.format(table))

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
    def consolidate_columns(list_of_dict, placeholder='ABSENT'):
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
