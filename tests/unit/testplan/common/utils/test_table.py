import pytest
from collections import namedtuple, OrderedDict
from testplan.common.utils.table import TableEntry, _TP_BLANK_CELL


@pytest.mark.skip(reason="new tests require this to fail")
class TestTableEntry(object):
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
            None,
            [[1, 2, 3], [1, 2, 3]],
            [["foo", "bar"], [1, 2], [3, 4]],
            [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}],
        ),
    )
    def test_validation_success(self, value):
        TableEntry(value)


_userio_params = ("description", "intable", "outtable")
UserInputOutput = namedtuple("UserInputOutput", _userio_params)

# Note that we need to use `OrderedDict` instead of `dict` to guarantee the
# column order of `outtable` for Python < 3.5
# fmt: off
# pylint: disable=line-too-long
@pytest.mark.parametrize(_userio_params, [
    UserInputOutput(
        "the same as the expected output table",
        intable=[
            ["a", "b", "c"],
            [1, 2, 3],
            [11, 22, 33],
        ],
        outtable=[
            [ "a", "b", "c" ],
            [  1,   2,   3  ],
            [  11,  22,  33 ],
        ],
    ),
    UserInputOutput(
        "a list of dicts",
        intable=[
            OrderedDict([
                ("a", 1),
                ("b", 2),
            ]),
            OrderedDict([
                ("a", 1),
                ("c", 3),
            ]),
        ],
        outtable=[
            [ "a", "b",            "c"             ],
            [  1,   2,              3              ],
            [  1,   _TP_BLANK_CELL, _TP_BLANK_CELL ],
        ],
    ),
    UserInputOutput(
        "a header-only list of lists",
        intable=[['a', 'b', 'c']],
        outtable=[['a', 'b', 'c']],
    ),
    UserInputOutput(
        "a list of one empty list",
        intable=[[]],
        outtable=[[]],
    ),
    UserInputOutput(
        "a list of an empty dict",
        intable=[{}],
        outtable=[[]],
    ),
    UserInputOutput(
        "an empty list",
        intable=[],
        outtable=[[]],
    ),
    UserInputOutput(
        "an empty dict",
        intable={},
        outtable=[[]],
    ),
])
# pylint: enable=line-too-long
# fmt: on
def test_table_inputs_standardized(description, intable, outtable):
    assert TableEntry(intable).table == outtable, (
        "Output table not as expected when input table is {}"
    ).format(description)
