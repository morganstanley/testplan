from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Dict, Generic, List, Tuple, TypeVar

try:
    from typing import Self  # starting from py311
except ImportError:
    from typing_extensions import Self


T = TypeVar("T")  # vertex rep
U = TypeVar("U")  # actual vertex
V = TypeVar("V")  # actual edge

GraphComponent = List[T]  # a component is a group of vertices


@dataclass
class DirectedGraph(Generic[T, U, V]):
    """
    Directed graph using adjacency matrix representation.
    """

    vertices: Dict[T, U]
    edges: Dict[T, Dict[T, V]]
    indegrees: Dict[T, int]
    outdegrees: Dict[T, int]

    @classmethod
    def new(cls) -> Self:
        """
        Construct an empty new graph.

        :return: The new graph.
        """
        return cls(dict(), dict(), dict(), dict())

    @classmethod
    def from_vertices(cls, vertices: Dict[T, U]) -> Self:
        """
        Construct a graph from its vertices.

        :param vertices: Vertices in the graph, should be a dictionary with
            keys of type vertex representation, and values of type vertex
            value.
        :return: The new graph.
        """
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
        """
        Construct a graph from its vertices and edges.

        :param vertices: Vertices in the graph, should be a dictionary with
            keys of type vertex representation, and values of type vertex
            value.
        :param edges: Edges in the graph, should be a dictionary with keys of
            type vertex-rep 2-tuple, in the format of ``(src, dst)``, and values
            of type edge value.
        :return: The new graph.
        """
        edges_ = {k: dict() for k in vertices}
        indegrees_ = {k: 0 for k in vertices}
        outdegrees_ = {k: 0 for k in vertices}
        for (src, dst), val in edges.items():
            edges_[src][dst] = val
            indegrees_[dst] += 1
            outdegrees_[src] += 1

        return cls(copy(vertices), edges_, indegrees_, outdegrees_)

    def add_vertex(self, rep: T, val: U) -> bool:
        """
        Add a new vertex to the graph.

        :param rep: Vertex representation, must be Hashable.
        :param val: (Possibly large) Vertex value.
        :return: A boolean value indicating whether operation is successful.
        """
        if rep in self.vertices:
            return False
        self.vertices[rep] = val
        self.edges[rep] = dict()
        self.indegrees[rep] = 0
        self.outdegrees[rep] = 0
        return True

    def add_edge(self, src: T, dst: T, val: V) -> bool:
        """
        Add a new edge to the graph.

        :param src: Representation of source vertex, must already exist in
            the graph.
        :param dst: Representation of destination vertex, must already exist
            in the graph.
        :param val: (Possibly large) Edge value.
        :return: A boolean value indicating whether operation is successful.
        """
        if (
            src not in self.edges
            or dst not in self.edges
            or dst in self.edges[src]
        ):
            return False
        self.edges[src][dst] = val
        self.indegrees[dst] += 1
        self.outdegrees[src] += 1
        return True

    def remove_vertex(self, rep: T) -> bool:
        """
        Remove an existing vertex from the graph.

        :param rep: Representation of the vertex to remove.
        :return: A boolean value indicating whether operation is successful.
        """
        if rep not in self.vertices:
            return False

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
        """
        Remove an existing edge from the graph.

        :param src: Representation of source vertex of the edge to remove.
        :param dst: Representation of destination vertex of the edge to remove.
        :return: A boolean value indicating whether operation is successful.
        """
        if (
            src not in self.edges
            or dst not in self.edges
            or dst not in self.edges[src]
        ):
            return False

        del self.edges[src][dst]
        self.outdegrees[src] -= 1
        self.indegrees[dst] -= 1
        return True

    def update_vertex(self, rep: T, new_val: U) -> bool:
        """
        Update an existing vertex with a new value.

        :param new_val: The new value of the vertex.
        :return: A boolean value indicating whether operation is successful.
        """
        if not rep in self.vertices:
            return False
        self.vertices[rep] = new_val
        return True

    def update_edge(self, src: T, dst: T, new_val: V) -> bool:
        """
        Update an existing edge with a new value.

        :param new_val: The new value of the edge.
        :return: A boolean value indicating whether operation is successful.
        """
        if (
            src not in self.edges
            or dst not in self.edges
            or dst not in self.edges[src]
        ):
            return False
        self.edges[src][dst] = new_val
        return True

    def tarjan_scc(self) -> Dict[T, GraphComponent[T]]:
        """
        Implementation of Tarjan's strongly connected components algorithm.
        Original paper: https://citeseerx.ist.psu.edu/doc/10.1.1.327.8418

        :return: A dictionary containing strongly connected components, with
            keys of type root vertex of component and values of type list of
            vertices in that component.
        """
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

    def cycles(self) -> List[GraphComponent]:
        """
        Get all the cycles in the graph. A vertex without self-loop is also
        considered as a strongly connected component, we rule those out here.

        :return: A list of cycles. A cycle here is a list of its vertices.
        """
        return [
            compo
            for _, compo in self.tarjan_scc().items()
            if len(compo) > 1 or compo[0] in self.edges[compo[0]]
        ]

    def zero_indegrees(self) -> List[T]:
        """
        Get all vertices with zero indegree.

        :return: A list of vertices.
        """
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

    def transpose(self) -> Self:
        """
        Get a transposed copy of the original graph.

        :return: The new graph.
        """
        transposed = self.__class__.from_vertices(self.vertices)
        for src, dst_d in self.edges.items():
            for dst, edge in dst_d.items():
                transposed.add_edge(dst, src, edge)
        return transposed
