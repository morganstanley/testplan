import copy
from itertools import product
from typing import TYPE_CHECKING, Generator, Iterable, List

from testplan.common.utils.graph import DirectedGraph

if TYPE_CHECKING:
    from testplan.testing.multitest.driver import Driver


def _type_err(msg: str) -> TypeError:
    return TypeError(
        f"Wrong type used in Testplan Driver dependencies definition. {msg}"
    )


class DriverDepGraph(DirectedGraph[str, "Driver", bool]):
    """
    An always acyclic directed graph, also bookkeeping driver starting status.
    """

    _starting = set()

    @classmethod
    def from_directed_graph(cls, g: DirectedGraph) -> "DriverDepGraph":
        if len(g.cycles()):
            raise ValueError(
                "Bad Testplan Driver dependency definition. "
                f"Cyclic dependency detected among {g.cycles()[0]}."
            )
        g_ = copy.copy(g)
        return cls(g_.vertices, g_.edges, g_.indegrees, g_.outdegrees)

    def mark_starting(self, driver: "Driver"):
        self._starting.add(driver.uid())

    def mark_started(self, driver: "Driver"):
        self._starting.remove(driver.uid())
        self.remove_vertex(driver.uid())

    def drivers_to_start(self) -> Generator["Driver", None, None]:
        for d in self.zero_indegrees():
            if d not in self._starting:
                yield self.vertices[d]

    def drivers_starting(self) -> List["Driver"]:
        return [self.vertices[d] for d in self._starting]

    def all_drivers_started(self) -> bool:
        return not len(self)

    def purge_drivers_to_start(self):
        """
        A somehow special graph operation.
        """
        self.vertices = {d: self.vertices[d] for d in self._starting}
        self.edges = {d: dict() for d in self.vertices}
        self.indegrees = {d: 0 for d in self.vertices}
        self.outdegrees = {d: 0 for d in self.vertices}


def parse_dependency(input: dict) -> DriverDepGraph:
    """
    The following dependency definition

    {
        A: (B, C),
        (B, C): [D, E],
        E: F,
    }

    will be parsed into

    {
        A: {B: True, C: True},
        B: {D: True, E: True},
        C: {D: True, E: True},
        E: {F: True},
    }
    """

    from testplan.testing.multitest.driver import Driver

    if not isinstance(input, dict):
        raise _type_err("Python dict expected.")

    g = DirectedGraph.new()

    for k, v in input.items():
        if not (
            isinstance(k, Driver)
            or (
                isinstance(k, Iterable)
                and all(isinstance(x, Driver) for x in k)
            )
        ):
            raise _type_err(
                "Driver or flat collection of Driver expected for dict keys."
            )

        if not (
            isinstance(v, Driver)
            or (
                isinstance(v, Iterable)
                and all(isinstance(x, Driver) for x in v)
            )
        ):
            raise _type_err(
                "Driver or flat collection of Driver expected for dict values."
            )

        if isinstance(k, Driver):
            k = (k,)
        if isinstance(v, Driver):
            v = (v,)

        for s, e in product(k, v):
            if s.uid() not in g.vertices:
                g.add_vertex(s.uid(), s)
            if e.uid() not in g.vertices:
                g.add_vertex(e.uid(), e)
            if e.uid() not in g.edges[s.uid()]:
                g.add_edge(s.uid(), e.uid(), True)

    return DriverDepGraph.from_directed_graph(g)
