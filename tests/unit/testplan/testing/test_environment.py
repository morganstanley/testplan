"""
Tests related to driver starting scheduling generated from dependencies.
"""

import pytest

from testplan.testing.environment import (
    DriverDepGraph,
    TestEnvironment,
    parse_dependency,
)
from testplan.testing.multitest.driver import Driver

PRE = object()
POST = object()


def driver_calls(*drivers):
    return [(PRE, d.name) for d in drivers] + [(POST, d.name) for d in drivers]


class CustomDriver(Driver):
    def __init__(self, name, callback=None, *args, **options):
        def pre_start(driver):
            if callback:
                callback(PRE, driver.name)

        def post_start(driver):
            if callback:
                callback(POST, driver.name)

        super().__init__(
            name, pre_start=pre_start, post_start=post_start, **options
        )


def test_legacy_driver_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    env.add(CustomDriver("a", m, async_start=True))
    env.add(CustomDriver("b", m))
    env.add(CustomDriver("c", m, async_start=True))
    env.start()
    m.assert_has_calls(
        [
            mocker.call(*t)
            for t in [
                (PRE, "a"),
                (PRE, "b"),
                (POST, "b"),
                (PRE, "c"),
                (POST, "a"),
                (POST, "c"),
            ]
        ]
    )


def test_graph_parser():
    a = CustomDriver("a")
    b = CustomDriver("b")
    c = CustomDriver("c")
    d = CustomDriver("d")
    e = CustomDriver("e")
    f = CustomDriver("f")
    g = CustomDriver("g")
    g_ = parse_dependency({(a, b): c, c: d, e: [d, g]})
    assert g_.vertices == {a, b, c, d, e, g}
    assert g_.edges == {(a, c), (b, c), (c, d), (e, d), (e, g)}


def test_graph_parser_exception():
    a = CustomDriver("a")
    b = CustomDriver("b")
    c = CustomDriver("c")
    with pytest.raises(TypeError, match=r".*dict expected.*"):
        parse_dependency([a, b])
    with pytest.raises(TypeError, match=r".*Driver.*expected.*dict values.*"):
        parse_dependency({a: "b"})


def test_bad_config_exception():
    env = TestEnvironment()
    env.add(CustomDriver("a", async_start=True))
    env.add(CustomDriver("b"))
    with pytest.raises(
        ValueError, match=r".*async_start.*should not be set.*"
    ):
        env.set_dependency(DriverDepGraph.new())


def test_unidentified_driver_exception():
    env = TestEnvironment()
    a = CustomDriver("a")
    b = CustomDriver("b")
    c = CustomDriver("c")
    env.add(a)
    env.add(b)
    with pytest.raises(ValueError, match=r".*drivers must be declared.*"):
        env.set_dependency(DriverDepGraph({a, b, c}, {(a, b)}))


def test_cyclic_dependency_exception():
    env = TestEnvironment()
    a = CustomDriver("a")
    b = CustomDriver("b")
    c = CustomDriver("c")
    for d_ in [a, b, c]:
        env.add(d_)
    with pytest.raises(ValueError, match=r".*cyclic dependency.*"):
        env.set_dependency(DriverDepGraph({a, b, c}, {(a, b), (b, c), (c, a)}))


def test_simple_dependency_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = CustomDriver("a", m)
    b = CustomDriver("b", m)
    c = CustomDriver("c", m)
    for d_ in [a, b, c]:
        env.add(d_)
    env.set_dependency(DriverDepGraph({a, b, c}, {(a, c), (b, c)}))
    env.start()
    m.assert_has_calls(
        [mocker.call(*t) for t in driver_calls(a, b) + driver_calls(c)]
    )


def test_complicated_dependency_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = CustomDriver("a", m)
    b = CustomDriver("b", m)
    c = CustomDriver("c", m)
    d = CustomDriver("d", m)
    e = CustomDriver("e", m)
    f = CustomDriver("f", m)
    g = CustomDriver("g", m)
    for d_ in [a, b, c, d, e, f, g]:
        env.add(d_)

    env.set_dependency(
        DriverDepGraph(
            {a, b, c, d, e, f, g},
            {(a, f), (b, f), (f, g), (e, g), (c, d), (d, e)},
        )
    )
    env.start()
    m.assert_has_calls(
        [
            mocker.call(*t)
            for t in driver_calls(a, b, c)
            + driver_calls(d, f)
            + driver_calls(e)
            + driver_calls(g)
        ]
    )
