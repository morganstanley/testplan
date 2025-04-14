from copy import copy

import pytest

from testplan.testing.environment import parse_dependency

from .common import MockDriver


def test_basic_graph():
    a = MockDriver("a")
    b = MockDriver("b")
    c = MockDriver("c")
    d = MockDriver("d")
    e = MockDriver("e")
    f = MockDriver("f")
    g_ = parse_dependency({(a, b): c, c: d, e: [d, f]})
    assert set(g_.vertices.values()) == {a, b, c, d, e, f}
    for s, e in {(a, c), (b, c), (c, d), (e, d), (e, f)}:
        # if edge doesn't exist, KeyError will be thrown
        assert g_.edges[id(s)][id(e)] is None


def test_empty_graph():
    g_ = parse_dependency({})
    assert len(g_.vertices) == 0


def test_bad_input():
    a = MockDriver("a")
    b = MockDriver("b")
    c = MockDriver("c")
    with pytest.raises(TypeError, match=r".*dict expected.*"):
        parse_dependency([a, b])
    with pytest.raises(TypeError, match=r".*Driver.*expected.*dict values.*"):
        parse_dependency({a: "b"})


def test_cyclic_dependency_exception():
    a = MockDriver("a")
    b = MockDriver("b")
    c = MockDriver("c")
    with pytest.raises(ValueError, match=r".*Cyclic dependency.*"):
        parse_dependency({a: b, b: c, c: a})


def test_graph_operation():
    d1 = MockDriver("d1")
    d2 = MockDriver("d2")
    d3 = MockDriver("d3")
    g = parse_dependency({d1: d2, d2: d3})
    g.mark_processing(d1)
    g_ = copy(g)
    assert id(d1) in g_.processing
    g.mark_processed(d1)
    g_ = copy(g)
    assert id(d1) in g_.processed
    assert id(d1) not in g_.vertices
    assert g_.edges[id(d2)][id(d3)] is None

    g_ = g.transpose()
    assert "d1" not in g_.processed
    assert g_.edges[id(d3)][id(d2)] is None
