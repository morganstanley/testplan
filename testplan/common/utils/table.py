"""Utilities for working with tables."""
import six
from six.moves import range
from collections import OrderedDict

# pylint: disable=import-error, no-name-in-module
if six.PY3:
    from collections.abc import Container, Mapping, Sequence
else:
    from collections import Container, Mapping, Sequence
# pylint: enable=import-error, no-name-in-module

_TP_BLANK_CELL = "_TP_BLANK_CELL"


def _is_nonstr_sequence(obj):
    return isinstance(obj, Sequence) and not isinstance(obj, six.string_types)


def _table_from_list_of_lists(list_of_lists):
    # type: (Sequence[Sequence[Any]]) -> List[List[Any]]
    std_tbl = []
    # all that needs to happen here is that each nested list must be padded to
    # the length of the longest list
    tbl_width = 0
    # this bit finds the longest row and filters out invalid elements
    for row in list_of_lists:
        # TODO: determine whether we should raise here, or whether we should
        #       try harder to guess what is meant by a non-list-like element
        if not _is_nonstr_sequence(row):
            continue
        new_row = list(row)
        std_tbl.append(new_row)
        tbl_width = max(tbl_width, len(new_row))
    for row in std_tbl:
        pad_cells = tbl_width - len(row)
        row.extend([_TP_BLANK_CELL] * pad_cells)
    if len(std_tbl) == 0:  # empty list
        return [[]]
    return std_tbl


def _table_from_list_of_dicts(list_of_dicts):
    dict_of_lists = OrderedDict()
    for dict_elem in list_of_dicts:
        for hdr, val in six.iteritems(dict_elem):
            dict_of_lists.setdefault(hdr, []).append(val)
    return _table_from_dict_of_lists(dict_of_lists)


def _table_from_dict_of_lists(dict_of_lists):
    # type: (Mapping[AnyStr, Any]) -> List[List[Any]]
    tbl_headers = list(six.iterkeys(dict_of_lists))
    n_hdrs = len(tbl_headers)
    if n_hdrs == 0:  # empty dict
        return [[]]
    new_prefilled_row = lambda: [_TP_BLANK_CELL] * n_hdrs
    tbl_data = [new_prefilled_row()]
    for col_idx, col_name in enumerate(tbl_headers):
        val = dict_of_lists[col_name]
        col_cells = list(val) if _is_nonstr_sequence(val) else [val]
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
        self._tbl_list_of_dict = None
        self._tbl_list_of_list = None
        if isinstance(table, Container):
            if isinstance(table, Mapping):
                new_tbl = OrderedDict(table)
                self._tbl_list_of_dict = new_tbl
                self._tbl_list_of_list = _table_from_dict_of_lists(new_tbl)
                return
            if _is_nonstr_sequence(table):
                new_tbl = list(table)
                if len(new_tbl) > 0 and isinstance(new_tbl[0], Mapping):
                    self._tbl_list_of_list = _table_from_list_of_dicts(new_tbl)
                    return
                self._tbl_list_of_list = _table_from_list_of_lists(new_tbl)
                return
        # if we're here then we've been passed an object that cannot be
        # interpreted as a table, so we return an empty table with
        # empty headers
        # TODO: determine whether we should raise an exception here
        self._tbl_list_of_list = [[]]
        return

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
        if self._tbl_list_of_dict is None:
            self._tbl_list_of_dict = []
            # if ``list`` of ``list``, then we convert to ``list`` of ``dict``
            # with dict elements indexed by headers
            _Map = OrderedDict if keep_column_order else dict
            headers = self._tbl_list_of_list[0]
            if len(self._tbl_list_of_list) > 1:
                for row in self._tbl_list_of_list[1:]:
                    self._tbl_list_of_dict.append(
                        _Map([(hdr, row[n]) for n, hdr in enumerate(headers)])
                    )
        return self._tbl_list_of_dict
