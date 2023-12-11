from dataclasses import dataclass
from functools import reduce
from typing import Generic, List, TypeVar

import testplan.common.utils.selector as S


def test_basic_op():
    assert S.apply_on_set(S.Not(S.Eq("a")), {"a", "b"}) == {"b"}
    assert S.apply_on_set(S.Not(S.Eq("a")), {"c", "b"}) == {"b", "c"}
    assert S.apply_on_set(
        S.Or2(S.Eq("a"), S.Eq("b")), {"a", "b", "c", "d"}
    ) == {"a", "b"}


def test_ext():

    X = TypeVar("X")

    @dataclass
    class AndN(Generic[X]):
        terms: List[X]

        def map(self, f):
            return AndN(list(map(f, self.terms)))

    to_reuse = S.eval_on_set({"a", "b", "c"})

    def _(x):
        if isinstance(x, AndN):
            return reduce(lambda x, y: x.intersection(y), x.terms)
        return to_reuse(x)

    assert S.cata(
        _,
        AndN(
            [
                S.Or2(S.Eq("a"), S.Eq("b")),
                S.Or2(S.Eq("b"), S.Eq("c")),
                S.Not(S.Eq("a")),
            ]
        ),
    ) == {"b"}
