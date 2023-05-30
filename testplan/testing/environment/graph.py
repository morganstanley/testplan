from copy import copy
from dataclasses import dataclass, field
from itertools import product
from typing import TYPE_CHECKING, Dict, Iterable, List, Set

from testplan.common.utils.graph import DirectedGraph

if TYPE_CHECKING:
    from testplan.testing.multitest.driver import Driver


def _type_err(msg: str) -> TypeError:
    return TypeError(
        f"Wrong type used in Testplan Driver dependencies definition. {msg}"
    )


@dataclass
class DriverDepGraph(DirectedGraph[str, "Driver", bool]):
    """
    An always acyclic directed graph, also bookkeeping driver starting status.
    """

    processing: Set["Driver"] = field(default_factory=set)
    processed: List["Driver"] = field(default_factory=list)

    @classmethod
    def from_directed_graph(cls, g: DirectedGraph) -> "DriverDepGraph":
        cycles = g.cycles()
        if len(cycles):
            raise ValueError(
                "Bad Testplan Driver dependency definition. "
                f"Cyclic dependency detected among {cycles[0]}."
            )
        g_ = copy(g)
        return cls(g_.vertices, g_.edges, g_.indegrees, g_.outdegrees)

    def mark_processing(self, driver: "Driver"):
        self.processing.add(driver.uid())

    def mark_processed(self, driver: "Driver"):
        self.processing.remove(driver.uid())
        self.remove_vertex(driver.uid())
        self.processed.append(driver.uid())

    def mark_failed_to_process(self, driver: "Driver"):
        self.processing.remove(driver.uid())
        self.remove_vertex(driver.uid())

    def drivers_to_process(self) -> List["Driver"]:
        return [
            self.vertices[d]
            for d in self.zero_indegrees()
            if d not in self.processing
        ]

    def drivers_processing(self) -> List["Driver"]:
        return [self.vertices[d] for d in self.processing]

    def all_drivers_processed(self) -> bool:
        return not len(self)

    def purge_drivers_to_process(self):
        """
        A graph operation which purges everything in the graph except for the
        drivers still in processing status.
        """
        self.vertices = {d: self.vertices[d] for d in self.processing}
        self.edges = {d: dict() for d in self.vertices}
        self.indegrees = {d: 0 for d in self.vertices}
        self.outdegrees = {d: 0 for d in self.vertices}

    def __copy__(self):
        obj = self.__class__(
            vertices=copy(self.vertices),
            edges={src: copy(dst) for src, dst in self.edges.items()},
            indegrees=copy(self.indegrees),
            outdegrees=copy(self.outdegrees),
        )
        obj.processing = copy(self.processing)
        obj.processed = copy(self.processed)
        return obj


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
        "A": {"B": None, "C": None},
        "B": {"D": None, "E": None},
        "C": {"D": None, "E": None},
        "E": {"F": None},
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
                g.add_edge(s.uid(), e.uid(), None)

    return DriverDepGraph.from_directed_graph(g)
