from dataclasses import dataclass
from functools import reduce
from typing import Generic, List, TypeVar

from testplan.common.utils import selector


def test_basic_op():
    assert selector.apply_single(selector.Not(selector.Eq("a")), "a") == False
    assert selector.apply_on_set(
        selector.Not(selector.Eq("a")), {"a", "b"}
    ) == {"b"}
    assert selector.apply_on_set(
        selector.Not(selector.Eq("a")), {"c", "b"}
    ) == {"b", "c"}
    assert selector.apply_on_set(
        selector.Or2(selector.Eq("a"), selector.Eq("b")), {"a", "b", "c", "d"}
    ) == {"a", "b"}


def test_ext():

    X = TypeVar("X")

    @dataclass
    class AndN(Generic[X]):
        terms: List[X]

        def map(self, f):
            return AndN(list(map(f, self.terms)))

    to_reuse = selector.eval_on_set({"a", "b", "c"})

    def _(x):
        if isinstance(x, AndN):
            return reduce(lambda x, y: x.intersection(y), x.terms)
        return to_reuse(x)

    assert selector.cata(
        _,
        AndN(
            [
                selector.Or2(selector.Eq("a"), selector.Eq("b")),
                selector.Or2(selector.Eq("b"), selector.Eq("c")),
                selector.Not(selector.Eq("a")),
            ]
        ),
    ) == {"b"}
