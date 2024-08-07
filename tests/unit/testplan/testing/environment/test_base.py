from unittest.mock import call

import pytest

from testplan.testing.environment import (
    DriverDepGraph,
    TestEnvironment,
    parse_dependency,
)

from .common import (
    FlakyDriver,
    MockDriver,
    assert_call_count,
    assert_lhs_before_rhs,
    assert_lhs_call_before_rhs_call,
)


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
    env.stop()


def test_set_dependency_none(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    env.add(MockDriver("a", m, async_start=True))
    env.add(MockDriver("b", m))
    env.set_dependency(None)
    env.start()
    m.assert_has_calls(
        [
            mocker.call.pre("a"),
            mocker.call.pre("b"),
            mocker.call.post("b"),
            mocker.call.post("a"),
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
        env.set_dependency(parse_dependency({a: (b, c)}))


def test_environment_restart(mocker):
    m = mocker.Mock()
    env = TestEnvironment()
    a = MockDriver("a", m)
    b = MockDriver("b", m)
    c = MockDriver("c", m)
    for d_ in [a, b, c]:
        env.add(d_)

    env.set_dependency(parse_dependency({a: b, b: c}))
    env.start()
    env.stop()
    env.start()
    assert_call_count(m.method_calls, call.pre("a"), 2)
    assert_call_count(m.method_calls, call.post("b"), 2)
    assert_call_count(m.method_calls, call.pre("c"), 2)
    env.stop()


class TestFastDrivers:
    def test_simple_dependency_scheduling(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m)
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: c, c: b}))
        env.start()
        assert env._rt_dependency.processed == ["a", "c", "b"]
        env.stop()
        assert env._rt_dependency.processed == ["b", "c", "a"]

    def test_empty_dependency(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m)
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({}))
        env.start()
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.pre("b"), call.pre("c")
        )
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.pre("c"), call.post("a")
        )
        env.stop()

    def test_no_dependency_default_first(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m)
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert_lhs_before_rhs(env._rt_dependency.processed, c, b)
        env.stop()
        assert_lhs_before_rhs(env._rt_dependency.processed, c, a)

    def test_complicated_dependency_scheduling(self, mocker):
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
        assert_lhs_before_rhs(env._rt_dependency.processed, a, d)
        assert_lhs_before_rhs(env._rt_dependency.processed, c, f)
        assert_lhs_before_rhs(env._rt_dependency.processed, f, e)
        assert_lhs_before_rhs(env._rt_dependency.processed, e, g)
        env.stop()
        assert_lhs_before_rhs(env._rt_dependency.processed, a, c)
        assert_lhs_before_rhs(env._rt_dependency.processed, f, c)
        assert_lhs_before_rhs(env._rt_dependency.processed, e, b)
        assert_lhs_before_rhs(env._rt_dependency.processed, g, e)


class TestSlowDrivers:
    def test_scheduling_1(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, total_wait=1)
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        d = MockDriver("d", m)
        for d_ in [a, b, c, d]:
            env.add(d_)

        env.set_dependency(parse_dependency({b: c, c: d}))
        env.start()
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.pre("b"), call.pre("a")
        )  # b is added to graph before a
        assert_lhs_before_rhs(env._rt_dependency.processed, b, c)
        assert_lhs_before_rhs(env._rt_dependency.processed, c, d)
        assert_lhs_before_rhs(env._rt_dependency.processed, d, a)
        env.stop()

    def test_scheduling_2(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, total_wait=0.5)
        b = MockDriver("b", m, total_wait=1)
        c = MockDriver("c", m)
        d = MockDriver("d", m)
        for d_ in [a, b, c, d]:
            env.add(d_)

        env.set_dependency(parse_dependency({(a, b): c, a: d}))
        env.start()
        assert_lhs_before_rhs(env._rt_dependency.processed, b, c)
        assert_lhs_before_rhs(env._rt_dependency.processed, d, c)
        env.stop()

    def test_scheduling_3(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, total_wait=0.5)
        b = MockDriver("b", m)
        c = MockDriver("c", m, check_interval=1)
        for d_ in [a, b, c]:
            env.add(d_)

        env.set_dependency(parse_dependency({}))
        env.start()
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.pre("a"), call.pre("b")
        )
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.pre("b"), call.pre("c")
        )
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.post("b"), call.post("a")
        )
        assert_lhs_call_before_rhs_call(
            m.method_calls, call.post("a"), call.post("c")
        )
        env.stop()


class TestExceptionThrown:
    def test_starting_failed(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m, pass_starting=False)
        b = FlakyDriver("b", m)
        c = FlakyDriver("c", m)

        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert len(env.start_exceptions) == 1
        assert a.status == a.status.STARTING
        assert b.status == b.status.NONE
        assert c.status == c.status.NONE
        env.stop()

    def test_started_check_failed(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m, pass_started_check=False)
        b = FlakyDriver("b", m)
        c = FlakyDriver("c", m)

        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert len(env.start_exceptions) == 1
        assert a.status == a.status.STARTING
        assert b.status == b.status.NONE
        assert c.status == c.status.STARTED
        env.stop()

    def test_stopping_failed(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m, pass_stopping=False)
        b = FlakyDriver("b", m)
        c = FlakyDriver("c", m)

        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert a.status == a.status.STARTED
        assert b.status == b.status.STARTED
        assert c.status == c.status.STARTED
        env.stop()
        assert len(env.stop_exceptions) == 1
        assert a.status == a.status.STOPPED
        assert b.status == b.status.STOPPED
        assert c.status == c.status.STOPPED

    def test_stopped_check_failed(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m, pass_stopped_check=False)
        b = FlakyDriver("b", m)
        c = FlakyDriver("c", m)

        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert a.status == a.status.STARTED
        assert b.status == b.status.STARTED
        assert c.status == c.status.STARTED
        env.stop()
        assert len(env.stop_exceptions) == 1
        assert a.status == a.status.STOPPED
        assert b.status == b.status.STOPPED
        assert c.status == c.status.STOPPED
