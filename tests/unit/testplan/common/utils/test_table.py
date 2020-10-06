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
        "a list of lists, some of which are shorter than the header",
        intable=[
            ["a", "b", "c"],
            [1, 2],
            [11, 22, 33],
            [111],
        ],
        outtable=[
            [ "a", "b",             "c"             ],
            [  1,   2,               _TP_BLANK_CELL ],
            [  11,  22,              33             ],
            [  111, _TP_BLANK_CELL,  _TP_BLANK_CELL ],
        ],
    ),
    UserInputOutput(
        "a list of lists, some of which are longer than the header",
        intable=[
            ["a", "b", "c"],
            [1, 2, 3, 4],
            [11, 22, 33],
            [111, 222, 333, 444, 555],
        ],
        outtable=[
            [ "a", "b", "c", _TP_BLANK_CELL, _TP_BLANK_CELL  ],
            [  1,   2,   3,   4,              _TP_BLANK_CELL ],
            [  11,  22,  33,  _TP_BLANK_CELL, _TP_BLANK_CELL ],
            [  111, 222, 333, 444,            555 ],
        ],
    ),
    UserInputOutput(
        (
            "a list of lists, some of which are longer than the header "
            "and some of which are shorter than the header"
        ),
        intable=[
            ["a", "b", "c"],
            [1, 2, 3, 4],
            [11],
            [111, 222, 333, 444, 555],
        ],
        outtable=[
            [ "a", "b",             "c",              _TP_BLANK_CELL, _TP_BLANK_CELL  ],
            [  1,   2,               3,               4,               _TP_BLANK_CELL ],
            [  11,  _TP_BLANK_CELL,  _TP_BLANK_CELL,  _TP_BLANK_CELL,  _TP_BLANK_CELL ],
            [  111, 222,             333,             444,             555            ],
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
    UserInputOutput(
        "a dict of empty lists",
        intable=OrderedDict([
            ("a", []),
            ("b", []),
            ("c", []),
        ]),
        outtable=[
            [ "a",           "b",            "c"             ],
            [ _TP_BLANK_CELL, _TP_BLANK_CELL, _TP_BLANK_CELL ],
        ],
    ),
    UserInputOutput(
        "a dict of equal-length lists",
        intable=OrderedDict([
            ("a", [1, 2, 3]),
            ("b", [11, 22, 33]),
            ("c", [111, 222, 333]),
        ]),
        outtable=[
            [ "a", "b", "c"  ],
            [  1,   11,  111 ],
            [  2,   22,  222 ],
            [  3,   33,  333 ],
        ],
    ),
    UserInputOutput(
        "a dict of unequal-length lists",
        intable=OrderedDict([
            ("a", [1, 2, 3, 4]),
            ("b", [11, 22]),
            ("c", [111, 222, 333]),
            ("d", []),
        ]),
        outtable=[
            [ "a", "b",             "c",            "d"             ],
            [  1,   11,              111,            _TP_BLANK_CELL ],
            [  2,   22,              222,            _TP_BLANK_CELL ],
            [  3,   _TP_BLANK_CELL,  333,            _TP_BLANK_CELL ],
            [  4,   _TP_BLANK_CELL,  _TP_BLANK_CELL, _TP_BLANK_CELL ],
        ],
    ),
    UserInputOutput(
        "a dict containing non-sequence values",
        intable=OrderedDict([
            ("a", 1),
            ("b", 'bbb'),
            ("c", [111, 222, 333]),
            ("d", dict()),
            ("e", set()),
        ]),
        outtable=[
            [ "a",            "b",            "c", "d",            "e"             ],
            [  1,              "bbb",          111, dict(),         set()          ],
            [  _TP_BLANK_CELL, _TP_BLANK_CELL, 222, _TP_BLANK_CELL, _TP_BLANK_CELL ],
            [  _TP_BLANK_CELL, _TP_BLANK_CELL, 333, _TP_BLANK_CELL, _TP_BLANK_CELL ],
        ],
    ),
])
# pylint: enable=line-too-long
# fmt: on
def test_table_inputs_standardized(description, intable, outtable):
    assert TableEntry(intable).table == outtable, (
        "Output table not as expected when input table is {}"
    ).format(description)
