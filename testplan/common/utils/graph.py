from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Dict, Generic, List, Tuple, TypeVar

try:
    from typing import Self  # starting from py311
except ImportError:
    from typing_extensions import Self

from memoization import cached

T = TypeVar("T")  # vertex rep
U = TypeVar("U")  # actual vertex
V = TypeVar("V")  # actual edge

GraphComponent = List[T]  # a component is a group of vertices


@dataclass
class DirectedGraph(Generic[T, U, V]):
    """adjacency matrix for directed graph"""

    vertices: Dict[T, U]
    edges: Dict[T, Dict[T, V]]
    indegrees: Dict[T, int]
    outdegrees: Dict[T, int]

    @classmethod
    def new(cls) -> Self:
        return cls(dict(), dict(), dict(), dict())

    @classmethod
    def from_vertices(cls, vertices: Dict[T, U]) -> Self:
        return cls(
            copy(vertices),
            {k: dict() for k in vertices},
            {k: 0 for k in vertices},
            {k: 0 for k in vertices},
        )

    @classmethod
    def from_vertices_and_edges(
        cls, vertices: Dict[T, U], edges: Dict[Tuple[T, T], V]
    ) -> Self:
        edges_ = {k: dict() for k in vertices}
        indegrees_ = {k: 0 for k in vertices}
        outdegrees_ = {k: 0 for k in vertices}
        for (src, dst), val in edges.items():
            edges_[src][dst] = val
            indegrees_[dst] += 1
            outdegrees_[src] += 1

        return cls(copy(vertices), edges_, indegrees_, outdegrees_)

    def __invalid(self):
        self.cycles.cache_clear()

    def add_vertex(self, rep: T, obj: U) -> bool:
        if rep in self.vertices:
            return False
        self.__invalid()
        self.vertices[rep] = obj
        self.edges[rep] = dict()
        self.indegrees[rep] = 0
        self.outdegrees[rep] = 0
        return True

    def add_edge(self, src: T, dst: T, edge_val: V) -> bool:
        if (
            src not in self.edges
            or dst not in self.edges
            or dst in self.edges[src]
        ):
            return False
        self.__invalid()
        self.edges[src][dst] = edge_val
        self.indegrees[dst] += 1
        self.outdegrees[src] += 1
        return True

    def remove_vertex(self, rep: T) -> bool:
        if rep not in self.vertices:
            return False

        self.__invalid()
        del self.vertices[rep]
        del self.indegrees[rep]
        del self.outdegrees[rep]

        for v in self.edges[rep]:
            self.indegrees[v] -= 1
        del self.edges[rep]

        for v in self.vertices:
            if rep in self.edges[v]:
                del self.edges[v][rep]
                self.outdegrees[v] -= 1
        return True

    def remove_edge(self, src: T, dst: T) -> bool:
        if (
            src not in self.edges
            or dst not in self.edges
            or dst not in self.edges[src]
        ):
            return False

        self.__invalid()
        del self.edges[src][dst]
        self.outdegrees[src] -= 1
        self.indegrees[dst] -= 1
        return True

    def update_vertex(self, rep: T, new_obj: U) -> bool:
        if not rep in self.vertices:
            return False
        self.vertices[rep] = new_obj
        return True

    def update_edge(self, src: T, dst: T, new_val: V) -> bool:
        if (
            src not in self.edges
            or dst not in self.edges
            or dst not in self.edges[src]
        ):
            return False
        self.edges[src][dst] = new_val
        return True

    def tarjan_scc(self) -> Dict[T, GraphComponent[T]]:
        """Tarjan's strongly connected components algorithm"""
        index = 0
        stack = []
        indices = dict(map(lambda x: (x, None), self.vertices.keys()))
        lowlink = dict(map(lambda x: (x, None), self.vertices.keys()))
        onstack = dict(map(lambda x: (x, False), self.vertices.keys()))
        ret_scc = defaultdict(list)

        def _strongly_connect(v):
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index = index + 1
            stack.append(v)
            onstack[v] = True

            for w in self.edges[v]:  # edge values not considered here
                if indices[w] is None:
                    _strongly_connect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif onstack[w]:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                # v is root vertex of certain scc
                while True:
                    w = stack.pop()
                    onstack[w] = False
                    ret_scc[v].append(w)
                    if w == v:
                        break

        for v in self.vertices:
            if indices[v] is None:
                _strongly_connect(v)

        return ret_scc

    @cached
    def cycles(self) -> List[GraphComponent]:
        return [
            compo
            for _, compo in self.tarjan_scc().items()
            if len(compo) > 1 or compo[0] in self.edges[compo[0]]
        ]

    def zero_indegrees(self) -> List[T]:
        return [v for v in self.vertices if self.indegrees[v] == 0]

    def __len__(self) -> int:
        return len(self.vertices)

    def __copy__(self) -> Self:
        return self.__class__(
            vertices=copy(self.vertices),
            edges={src: copy(dst) for src, dst in self.edges.items()},
            indegrees=copy(self.indegrees),
            outdegrees=copy(self.outdegrees),
        )
