import pytest

from testplan.testing.environment import (
    DriverDepGraph,
    TestEnvironment,
    parse_dependency,
)

from .common import MockDriver, assert_lhs_before_rhs


def test_legacy_driver_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    env.add(MockDriver("a", m, async_start=True))
    env.add(MockDriver("b", m))
    env.add(MockDriver("c", m, async_start=True))
    env.start()
    m.assert_has_calls(
        [
            mocker.call.pre("a"),
            mocker.call.pre("b"),
            mocker.call.post("b"),
            mocker.call.pre("c"),
            mocker.call.post("a"),
            mocker.call.post("c"),
        ]
    )


def test_bad_config_exception():
    env = TestEnvironment()
    env.add(MockDriver("a", async_start=True))
    env.add(MockDriver("b"))
    with pytest.raises(
        ValueError, match=r".*async_start.*should not be set.*"
    ):
        env.set_dependency(DriverDepGraph.new())


def test_unidentified_driver_exception():
    env = TestEnvironment()
    a = MockDriver("a")
    b = MockDriver("b")
    c = MockDriver("c")
    env.add(a)
    env.add(b)
    with pytest.raises(ValueError, match=r".*not being declared.*"):
        env.set_dependency(parse_dependency({a: b, a: c}))


def test_simple_dependency_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = MockDriver("a", m)
    b = MockDriver("b", m)
    c = MockDriver("c", m)
    for d_ in [a, b, c]:
        env.add(d_)
    env.set_dependency(parse_dependency({a: c, b: c}))
    env.start()
    assert_lhs_before_rhs(m.method_calls, a, c)
    assert_lhs_before_rhs(m.method_calls, b, c)


def test_no_dependency_default_first(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = MockDriver("a", m)
    b = MockDriver("b", m)
    c = MockDriver("c", m)
    for d_ in [a, b, c]:
        env.add(d_)
    env.set_dependency(parse_dependency({a: b}))
    env.start()
    assert_lhs_before_rhs(m.method_calls, c, b)


def test_complicated_dependency_scheduling(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = MockDriver("a", m)
    b = MockDriver("b", m)
    c = MockDriver("c", m)
    d = MockDriver("d", m)
    e = MockDriver("e", m)
    f = MockDriver("f", m)
    g = MockDriver("g", m)
    for d_ in [a, b, c, d, e, f, g]:
        env.add(d_)

    env.set_dependency(
        parse_dependency(
            {a: f, b: f, f: g, e: g, c: d, d: e},
        )
    )
    env.start()
    assert_lhs_before_rhs(m.method_calls, a, d)
    assert_lhs_before_rhs(m.method_calls, c, f)
    assert_lhs_before_rhs(m.method_calls, f, e)
    assert_lhs_before_rhs(m.method_calls, e, g)
