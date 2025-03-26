import pytest
from itertools import count

from testplan.common.utils.interface import (
    check_signature_leading,
    check_signature,
    MethodSignatureMismatch,
)


def obj_a(a, /, b, *c, d, **e):
    pass


def obj_b(_a, /, _, *c, d, **e):
    pass


@pytest.mark.parametrize(
    "callable, exp_args, passed",
    [
        (obj_a, ["a"], False),
        (obj_a, ["a", "b"], True),
        (obj_a, ["a", "e"], False),
        (obj_a, ["a", "b", "c"], False),
        (obj_a, ["a", "b", "c", "d"], False),
        (obj_a, ["a", "b", "c", "d", "e"], False),
        (obj_b, ["a"], False),
        (obj_b, ["a", "b"], True),
        (obj_b, ["a", "e"], True),
        (obj_b, ["a", "b", "c"], False),
        (obj_b, ["a", "b", "c", "d"], False),
        (obj_b, ["a", "b", "c", "d", "e"], False),
    ],
    ids=count(0),
)
def test_check_signature(callable, exp_args, passed):
    if not passed:
        with pytest.raises(MethodSignatureMismatch):
            check_signature(callable, exp_args)
    else:
        assert check_signature(callable, exp_args)


@pytest.mark.parametrize(
    "callable, exp_args, passed",
    [
        (obj_a, ["a"], True),
        (obj_a, ["a", "b"], True),
        (obj_a, ["a", "e"], False),
        (obj_a, ["a", "b", "c"], False),
        (obj_b, ["a"], True),
        (obj_b, ["a", "b"], True),
        (obj_b, ["a", "e"], True),
        (obj_b, ["a", "b", "c"], False),
    ],
    ids=count(0),
)
def test_check_signature_leading(callable, exp_args, passed):
    if not passed:
        with pytest.raises(MethodSignatureMismatch):
            check_signature_leading(callable, exp_args)
    else:
        assert check_signature_leading(callable, exp_args)
