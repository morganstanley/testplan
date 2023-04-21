import pytest

from testplan.testing.environment import parse_dependency

from .common import MockDriver


def test_graph_parser():
    a = MockDriver("a")
    b = MockDriver("b")
    c = MockDriver("c")
    d = MockDriver("d")
    e = MockDriver("e")
    f = MockDriver("f")
    g = MockDriver("g")
    g_ = parse_dependency({(a, b): c, c: d, e: [d, g]})
    assert set(g_.vertices.values()) == {a, b, c, d, e, g}
    for s, e in {(a, c), (b, c), (c, d), (e, d), (e, g)}:
        assert g_.edges[s.name][e.name]


def test_graph_parser_exception():
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
