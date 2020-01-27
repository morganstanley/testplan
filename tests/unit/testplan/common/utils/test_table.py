import pytest
from testplan.common.utils.table import TableEntry


class TestTableEntry(object):
    @pytest.mark.parametrize(
        "value",
        (
            object(),
            {1, 2, 3},
            {"foo": "bar"},
            [1, 2, 3],
            [[1, 2, 3], [1, 2, 3]],
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
            None,
            [["foo", "bar"], [1, 2], [3, 4]],
            [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}],
        ),
    )
    def test_validation_success(self, value):
        TableEntry(value)
