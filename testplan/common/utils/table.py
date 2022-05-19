"""Utilities for working with tables."""

import collections


class TableEntry:
    """
    Represents a table. Internally represented either
    as a ``list`` of ``list`` or a ``list`` of ``dict``.
    """

    def __init__(self, source, placeholder=None):
        self._source = source
        self._placeholder = placeholder

        self._validate_input()

        if self._source and isinstance(self._source[0], (list, tuple)):
            self._columns = self._source[0]

    @property
    def columns(self):
        """Get column names."""
        if not self._source:
            return []
        if isinstance(self._source[0], (list, tuple)):
            return self._source[0]
        elif isinstance(self._source[0], dict):
            result = []
            for row in self._source:
                result.extend([key for key in row.keys() if key not in result])
            return result
        else:
            raise ValueError("Not a valid table")

    def _validate_input(self):
        if isinstance(self._source, (list, tuple)) and (
            all(isinstance(row, dict) for row in self._source)
            or all(isinstance(row, (list, tuple)) for row in self._source)
        ):
            return

        raise TypeError(
            f"`table` must be a list of lists or list of dicts, got:\n{self._source}"
        )

    def as_list_of_list(self):
        """
        Returns the table as ``list`` of ``list``

        :return: the table
        :rtype: ``list`` of ``list`` for the table

        """

        if len(self._source) and isinstance(self._source[0], dict):
            union = collections.OrderedDict()
            for row in self._source:
                union.update(row)
            columns = union.keys()

            table = [columns]
            for row in self._source:
                table.append(
                    [row.get(col, self._placeholder) for col in columns]
                )
            return table
        else:
            return self._source

    def as_list_of_dict(self):
        """
        Returns the table as ``list`` of ``dict``

        :return: the table
        :rtype: ``list`` of ``dict`` for the table
        """

        if len(self._source) and isinstance(self._source[0], (list, tuple)):
            table = []
            columns = self._source[0]
            for row in self._source[1:]:
                table.append(
                    collections.OrderedDict(
                        (col, row[idx])
                        for idx, col in enumerate(columns)
                        if not row[idx] is self._placeholder
                    )
                )
            return table
        else:
            return self._source

    def __len__(self):
        if len(self._source) and isinstance(self._source[0], (list, tuple)):
            return len(self._source) - 1
        else:
            return len(self._source)
