from testplan.common.utils.graph import DirectedGraph


class TestBasicOperation:
    def test_add_vertex(self):
        g = DirectedGraph.new()
        assert g.add_vertex(1, {"a": "b"})
        assert len(g) == 1
        assert g.vertices[1] == {"a": "b"}
        assert g.edges[1] == {}
        assert g.indegrees[1] == 0
        assert g.outdegrees[1] == 0
        assert not g.add_vertex(1, {"c": "d"})

    def test_remove_vertex(self):
        g = DirectedGraph.from_vertices({1: "a", 2: "b"})
        assert len(g) == 2
        assert not g.remove_vertex(3)
        assert g.remove_vertex(1)
        assert 1 not in g.vertices
        assert 1 not in g.indegrees
        assert not g.remove_vertex(1)

    def test_update_vertex(self):
        g = DirectedGraph.from_vertices({1: "a"})
        assert g.update_vertex(1, "b")
        assert not g.update_vertex(2, "a")

    def test_add_edge(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: 2, 3: 4}, {(1, 3): (1, 3)}
        )
        assert not g.add_edge(1, 3, tuple())
        assert not g.add_edge(2, 4, tuple())
        assert not g.add_edge(1, 2, tuple())
        assert g.indegrees[3] == 1
        assert g.outdegrees[1] == 1
        assert g.edges[1][3] == (1, 3)
        assert g.add_edge(3, 1, (3, 1))
        assert g.indegrees[1] == 1
        assert g.outdegrees[3] == 1

    def test_remove_edge(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: 2, 3: 4, 5: 6, 7: 8},
            {(1, 3): (1, 3), (3, 5): (3, 5), (1, 7): (1, 7)},
        )
        assert g.outdegrees[1] == 2
        assert g.remove_edge(1, 3)
        assert not g.remove_edge(1, 3)
        assert not g.remove_edge(1, 2)
        assert not g.remove_edge(4, 1)
        assert g.outdegrees[1] == 1

    def test_update_edge(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: 2, 3: 4, 5: 6}, {(1, 5): (1, 5), (5, 3): (5, 3)}
        )
        assert g.update_edge(1, 5, (5, 1))
        assert g.update_edge(5, 3, (3, 5))
        assert not g.update_edge(3, 5, (5, 3))
        assert not g.update_edge(1, 4, (4, 1))
        assert not g.update_edge(4, 1, (1, 4))

    def test_shallow_copy(self):
        v = {"a": 1, "b": 2}
        g = DirectedGraph.from_vertices(v)
        assert g.remove_vertex("a")
        assert set(v.keys()) == {"a", "b"}


class TestSCCOperations:
    def test_tarjan_scc(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: None, 2: None, 3: None, 4: None, 5: None, 6: None},
            {(2, 4): None, (4, 2): None},
        )
        sccs = g.tarjan_scc()
        assert 3 in sccs
        assert sccs[3] == [3]
        assert sccs[2] == [4, 2]

    def test_cycles(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: None, 2: None, 3: None, 4: None, 5: None, 6: None},
            {(2, 4): None, (4, 2): None, (6, 6): None},
        )
        assert len(g.cycles()) == 2
        assert set(tuple(sorted(c)) for c in g.cycles()) == {(2, 4), (6,)}

    def test_cycles_cache_invalidate(self):
        g = DirectedGraph.from_vertices_and_edges(
            {1: None, 2: None, 3: None, 4: None},
            {(1, 2): None, (2, 3): None, (3, 4): None, (4, 2): None},
        )
        assert len(g.cycles()) == 1
        assert set(g.cycles()[0]) == {2, 3, 4}
        assert g.add_edge(4, 1, None)
        assert set(g.cycles()[0]) == {1, 2, 3, 4}
        assert g.add_vertex(5, None)
        assert g.add_edge(1, 5, None)
        assert g.add_edge(5, 1, None)
        assert set(g.cycles()[0]) == {1, 2, 3, 4, 5}
        assert g.remove_edge(4, 1)
        assert len(g.cycles()) == 2
        assert set(tuple(sorted(c)) for c in g.cycles()) == {(2, 3, 4), (1, 5)}
