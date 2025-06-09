"""
Python module as a test subject for the tracing tests feature.

While its content doesn't really matter, this module contains a lazily-
evaluated version of Python list together with its related operations.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Type, Union

Boxed = Callable[[], Any]


def box(val: Any) -> Boxed:
    return lambda: val


def unbox(bval: Boxed) -> Any:
    return bval()


LList = Union["Cons", Type["Nil"]]

Nil = object()


@dataclass
class Cons:
    head: Boxed
    tail: LList


def to_lazy(li: List) -> LList:
    if not li:
        return Nil
    return Cons(box(li[0]), to_lazy(li[1:]))


def unlazy(lli: LList) -> List:
    if lli is Nil:
        return []
    return [unbox(lli.head), *unlazy(lli.tail)]


def lazy_len(lli: LList) -> int:
    if lli is Nil:
        return 0
    return 1 + lazy_len(lli.tail)


def lazy_get(lli: LList, ind: int) -> Boxed:
    if lli is Nil or ind < 0:
        raise RuntimeError("whoops")
    if ind == 0:
        return lli.head
    else:
        return lazy_get(lli.tail, ind - 1)


def lazy_apply(
    op: Callable[[Any, Any], Any], bval1: Boxed, bval2: Boxed
) -> Boxed:
    # doesn't look good enough though
    def _():
        val1 = unbox(bval1)
        val2 = unbox(bval2)
        return op(val1, val2)

    return _


def lazy_zip_with(
    op: Callable[[Any, Any], Any], lli1: LList, lli2: LList
) -> LList:
    if lli1 is Nil or lli2 is Nil:
        return Nil
    return Cons(
        lazy_apply(op, lli1.head, lli2.head),
        lazy_zip_with(op, lli1.tail, lli2.tail),
    )
