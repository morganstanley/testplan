"""Utilities for working with tables."""
import six
from collections import OrderedDict
from pprint import pformat

# pylint: disable=import-error, no-name-in-module
if six.PY3:
    from collections.abc import Mapping, Sequence
else:
    from collections import Mapping, Sequence
# pylint: enable=import-error, no-name-in-module

_TP_BLANK_CELL = "_TP_BLANK_CELL"


def _table_from_list_of_dicts(list_of_dicts):
    dict_of_lists = OrderedDict()
    for dict_elem in list_of_dicts:
        for hdr, val in six.iteritems(dict_elem):
            dict_of_lists.setdefault(hdr, []).append(val)
    tbl_headers = list(six.iterkeys(dict_of_lists))
    n_hdrs = len(tbl_headers)
    if n_hdrs == 0:  # empty dict
        return [[]]
    new_prefilled_row = lambda: [_TP_BLANK_CELL] * n_hdrs
    tbl_data = [new_prefilled_row()]
    for col_idx, col_name in enumerate(tbl_headers):
        val = dict_of_lists[col_name]
        col_cells = list(val) if isinstance(val, (list, tuple)) else [val]
        for row_idx, cell_val in enumerate(col_cells):
            # 1st iteration:
            #   (a) `row_idx` == 0, `len(tbl_data)` == 1
            #   (b) set `tbl_data[0][col_idx]` to `cell_val`
            # 2nd iteration:
            #   (a) `row_idx` == 1, `len(tbl_data)` == 1
            #   (b) inject a filler row into `tbl_data`
            #   (c) `row_idx` == 1, `len(tbl_data)` == 2 now
            #   (d) set `tbl_data[1][col_idx]` to `cell_val`
            # and so on..
            if len(tbl_data) == row_idx:
                tbl_data.append(new_prefilled_row())
            tbl_data[row_idx][col_idx] = cell_val
    return [tbl_headers] + tbl_data


class TableEntry(object):
    """
    Represents a table. Internally represented as ``List[List[Any]]``.
    """

    def __init__(self, table):
        self._tbl_list_of_list = []
        err_msg = (
            "`table` must be a nonempty tuple / list of "
            "tuples / lists of uniform length, or a tuple / list of "
            "dicts. Got:\n{}".format(pformat(table))
        )
        if not isinstance(table, (list, tuple)):
            raise TypeError(err_msg)
        if len(table) == 0:
            self._tbl_list_of_list.append([])
        elif isinstance(table[0], Mapping):
            list_of_dict = []
            for mapp in table:
                if not isinstance(mapp, Mapping):
                    raise TypeError(err_msg)
                list_of_dict.append(OrderedDict(mapp))
            self._tbl_list_of_list = _table_from_list_of_dicts(list_of_dict)
        else:
            width = len(table[0])
            for row in table:
                if not (isinstance(row, (list, tuple)) and len(row) == width):
                    raise TypeError(err_msg)
                self._tbl_list_of_list.append(list(row))

    def __len__(self):
        return len(self._tbl_list_of_list) - 1

    @property
    def table(self):
        return self._tbl_list_of_list

    @property
    def column_names(self):
        """
        Returns the column names of the table

        :return: the column names
        :rtype: ``list`` of ``str``
        """
        return self._tbl_list_of_list[0]

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
        return self._tbl_list_of_list

    def as_list_of_dict(self, keep_column_order=False):
        """
        Returns the table as ``list`` of ``dict``

        :return: the table
        :rtype: ``list`` of ``dict`` for the table
        """
        list_of_dict = []
        _Map = OrderedDict if keep_column_order else dict
        headers = self._tbl_list_of_list[0]
        if len(self._tbl_list_of_list) > 1:
            for row in self._tbl_list_of_list[1:]:
                list_of_dict.append(
                    _Map([(hdr, row[n]) for n, hdr in enumerate(headers)])
                )
        return list_of_dict
