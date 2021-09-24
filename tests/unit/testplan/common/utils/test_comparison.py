import pytest
from testplan.common.utils import comparison as cmp

from testplan.common.utils.reporting import Absent
import copy


def test_absent():
    assert id(Absent) == id(copy.deepcopy(Absent))


@pytest.mark.parametrize(
    "callable_kls,reference,value,expected,description",
    (
        (cmp.Less, 5, 2, True, "VAL < 5"),
        (cmp.Less, 1, 2, False, "VAL < 1"),
        (cmp.LessEqual, 5, 5, True, "VAL <= 5"),
        (cmp.LessEqual, 3, 5, False, "VAL <= 3"),
        (cmp.Greater, 3, 5, True, "VAL > 3"),
        (cmp.Greater, 3, 2, False, "VAL > 3"),
        (cmp.GreaterEqual, 3, 3, True, "VAL >= 3"),
        (cmp.GreaterEqual, 10, 3, False, "VAL >= 10"),
        (cmp.Equal, 1, 1, True, "VAL == 1"),
        (cmp.Equal, "aaa", "bbb", False, "VAL == aaa"),
        (cmp.NotEqual, 1, 2, True, "VAL != 1"),
        (cmp.NotEqual, 2, 2, False, "VAL != 2"),
        (cmp.In, [1, 2, 3], 1, True, "VAL in [1, 2, 3]"),
        (cmp.In, [1, 2, 3], 5, False, "VAL in [1, 2, 3]"),
        (cmp.NotIn, [1, 2, 3], 5, True, "VAL not in [1, 2, 3]"),
        (cmp.NotIn, [1, 2, 3], 3, False, "VAL not in [1, 2, 3]"),
    ),
)
def test_operator_callable(
    callable_kls, reference, value, expected, description
):
    callable_obj = callable_kls(reference)
    assert str(callable_obj) == description
    assert callable_obj(value) == expected


@pytest.mark.parametrize(
    "callable_kls,value,expected,description",
    (
        (cmp.IsTrue, 1, True, "bool(VAL) is True"),
        (cmp.IsTrue, 0, False, "bool(VAL) is True"),
        (cmp.IsFalse, 0, True, "bool(VAL) is False"),
        (cmp.IsFalse, 100, False, "bool(VAL) is False"),
    ),
)
def test_boolean_callable(callable_kls, value, expected, description):
    callable_obj = callable_kls()
    assert callable_obj(value) == expected
    assert str(callable_obj) == description


def test_custom_callable():
    custom_callable = cmp.Custom(
        lambda value: value % 2 == 0, description="Value is even."
    )

    assert custom_callable(4) == True
    assert str(custom_callable) == "Value is even."


@pytest.mark.parametrize(
    "composed_callable,value,expected,description",
    (
        (cmp.LessEqual(5) & cmp.Greater(2), 4, True, "(VAL <= 5 and VAL > 2)"),
        (
            cmp.In([1, 2, 3]) | cmp.Equal(None),
            None,
            True,
            "(VAL in [1, 2, 3] or VAL == None)",
        ),
        (
            cmp.And(
                cmp.Or(cmp.Equal("foo"), cmp.In([1, 2, 3]), cmp.Less(10)),
                cmp.Or(cmp.Greater(5), cmp.IsFalse()),
            ),
            8,
            True,
            "((VAL == foo or VAL in [1, 2, 3] or "
            "VAL < 10) and (VAL > 5 or bool(VAL) is False))",
        ),
    ),
)
def test_comparator_composition(
    composed_callable, value, expected, description
):
    assert composed_callable(value) == expected
    assert str(composed_callable) == description
