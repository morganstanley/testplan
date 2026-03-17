"""
inspired by recursion schemes from the functional programming world, to de-
couple represetation (of operators) from evaluation (of them on different
types)

see https://blog.sumtypeofway.com/posts/introduction-to-recursion-schemes.html

unlike statically-typed languages, python doesn't need a representation for
a possibly infinite recursively type, thus we omit a "fixed-point" type here

typevar in current python always of kind *, type hint won't work much here
"""

from dataclasses import dataclass
from typing import Any, Callable, Generic, Set, TypeVar

from typing_extensions import Protocol, Self

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
U = TypeVar("U")


class Functor(Protocol, Generic[T_co]):
    def map(self, f: Callable[[Any], Any]) -> Self:
        # map :: f t -> (t -> u) -> f u
        ...


@dataclass
class And2(Generic[T]):
    # logic and accepting 2 operands
    lterm: T
    rterm: T

    def map(self, f: Callable[[T], Any]) -> "And2[Any]":
        return And2(f(self.lterm), f(self.rterm))


@dataclass
class Or2(Generic[T]):
    # logic or accepting 2 operands
    lterm: T
    rterm: T

    def map(self, f: Callable[[T], Any]) -> "Or2[Any]":
        return Or2(f(self.lterm), f(self.rterm))


@dataclass
class Not(Generic[T]):
    term: T

    def map(self, f: Callable[[T], Any]) -> "Not[Any]":
        return Not(f(self.term))


@dataclass
class Eq(Generic[U]):
    val: U

    def map(self, _: Callable[[Any], Any]) -> "Eq[U]":
        return self


@dataclass
class Const(Generic[T]):
    val: bool

    def map(self, _: Callable[[Any], Any]) -> "Const[T]":
        return self


Expr = TypeVar("Expr", bound=Functor)


def cata(f: Callable[[Any], Any], rep: Any) -> Any:
    # i.e. catamorphism
    # cata :: (f t -> t) -> f (f (f ...)) -> t
    return f(rep.map(lambda x: cata(f, x)))


def eval_on_set(s: Set[Any]) -> Callable[[Any], Any]:
    def _(x: Any) -> Any:
        if isinstance(x, Const):
            return {i for i in s if x.val}
        if isinstance(x, Eq):
            return {i for i in s if i == x.val}
        if isinstance(x, And2):
            return x.lterm & x.rterm
        if isinstance(x, Or2):
            return x.lterm | x.rterm
        if isinstance(x, Not):
            return s - x.term
        raise TypeError(f"unexpected {x}")

    return _


def apply_on_set(rep: Any, s: Set[Any]) -> Set[Any]:
    result: Set[Any] = cata(eval_on_set(s), rep)
    return result


def apply_single(rep: Any, i: Any) -> bool:
    def _(x: Any) -> Any:
        if isinstance(x, Const):
            return x.val
        if isinstance(x, Eq):
            return x.val == i
        if isinstance(x, And2):
            return x.lterm and x.rterm
        if isinstance(x, Or2):
            return x.lterm or x.rterm
        if isinstance(x, Not):
            return not x.term
        raise TypeError(f"unexpected {x}")

    result: bool = cata(_, rep)
    return result
