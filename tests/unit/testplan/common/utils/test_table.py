from collections import OrderedDict

import pytest
from testplan.common.utils.table import TableEntry


class TestTableEntry:
    @pytest.mark.parametrize(
        "value",
        (
            object(),
            {1, 2, 3},
            {"foo": "bar"},
            [1, 2, 3],
            [["foo", "bar"], [1, 2], {"foo": "bar"}],
        ),
    )
    def test_validation_failure(self, value):
        with pytest.raises(TypeError):
            TableEntry(table=value)

    @pytest.mark.parametrize(
        "value",
        (
            tuple(),
            [],
            [[1, 2, 3], [1, 2, 3]],
            [["foo", "bar"], [1, 2], [3, 4]],
            [["foo", "bar"], [1, None], [None, 4]],
            [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}],
            [{"foo": 1}, {"bar": 4}],
        ),
    )
    def test_validation_success(self, value):
        TableEntry(value)

    @pytest.mark.parametrize(
        "value, expected",
        (
            (tuple(), []),
            ([], []),
            ([[1, 2, 3], [1, 2, 3]], [1, 2, 3]),
            ([["foo", "bar"], [1, 2], [3, 4]], ["foo", "bar"]),
            ([["foo", "bar"], [1, None], [None, 4]], ["foo", "bar"]),
            (
                [
                    OrderedDict([("foo", 1), ("bar", 2)]),
                    OrderedDict([("bar", 4), ("foo", 3)]),
                ],
                ["foo", "bar"],
            ),
            ([{"foo": 1}, {"bar": 4}], ["foo", "bar"]),
        ),
    )
    def test_table_columns(self, value, expected):
        assert TableEntry(value).columns == expected
