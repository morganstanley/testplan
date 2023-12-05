from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

# TODO: a la carte
SExpr = Union["And2", "Or2", "Not", "Lit", "_SExpr"]


class _SExpr(ABC):
    @abstractmethod
    def eval(self, x) -> bool:
        pass


@dataclass
class And2(_SExpr):
    lexpr: SExpr
    rexpr: SExpr

    def eval(self, x) -> bool:
        return self.lexpr.eval(x) and self.rexpr.eval(x)


@dataclass
class Or2(_SExpr):
    lexpr: SExpr
    rexpr: SExpr

    def eval(self, x) -> bool:
        return self.lexpr.eval(x) or self.rexpr.eval(x)


@dataclass
class Not(_SExpr):
    expr: SExpr

    def eval(self, x) -> bool:
        return not self.expr.eval(x)


@dataclass
class Lit(_SExpr):
    val: str

    def eval(self, x) -> bool:
        return self.val == x
