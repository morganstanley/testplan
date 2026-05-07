import time
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
        assert env._rt_dependency.processed == [id(a), id(c), id(b)]
        env.stop()
        assert env._rt_dependency.processed == [id(b), id(c), id(a)]

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
        a = MockDriver("a", m, total_start_wait=1)
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
        a = MockDriver("a", m, total_start_wait=0.5)
        b = MockDriver("b", m, total_start_wait=2)
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
        a = MockDriver("a", m, total_start_wait=0.5)
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
        assert "While starting driver FlakyDriver[a]:" in str(
            list(env.start_exceptions.values())[0]
        )
        assert a.status == a.status.STARTING
        assert b.status == b.status.NONE
        assert c.status == c.status.STARTED
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
        assert "While waiting for driver FlakyDriver[a] to start:" in str(
            list(env.start_exceptions.values())[0]
        )
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
        assert "While stopping driver FlakyDriver[a]:" in str(
            list(env.stop_exceptions.values())[0]
        )
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
        assert "While waiting for driver FlakyDriver[a] to stop:" in str(
            list(env.stop_exceptions.values())[0]
        )
        assert a.status == a.status.STOPPED
        assert b.status == b.status.STOPPED
        assert c.status == c.status.STOPPED

    def test_timeout_ordinary(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, total_start_wait=2, timeout=1)
        b = MockDriver("b", m)

        for d_ in [a, b]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert len(env.start_exceptions) == 1
        assert "Timeout when starting MockDriver[a]." in str(
            list(env.start_exceptions.values())[0]
        )
        assert a.status == a.status.STARTING
        assert b.status == b.status.NONE
        env.stop()

    def test_timeout_critical(self, mocker):
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, check_wait=2, timeout=1)
        b = MockDriver("b", m)

        for d_ in [a, b]:
            env.add(d_)
        env.set_dependency(parse_dependency({a: b}))
        env.start()
        assert len(env.start_exceptions) == 0
        assert a.status == a.status.STARTED
        assert b.status == b.status.STARTED
        env.stop()

    def test_both_failures_recorded(self, mocker):
        """
        Two independent drivers both fail in `starting` simultaneously.
        Both exceptions must be captured in ``env.start_exceptions``.
        An independent third driver must still reach STARTED.
        """
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m, pass_starting=False)
        b = FlakyDriver("b", m, pass_starting=False)
        c = FlakyDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({}))
        env.start()

        assert len(env.start_exceptions) == 2
        keys = list(env.start_exceptions.keys())
        assert a in keys and b in keys
        for drv in (a, b):
            assert "While starting driver FlakyDriver[{}]:".format(
                drv.name
            ) in str(env.start_exceptions[drv])
        assert a.status == a.status.STARTING
        assert b.status == b.status.STARTING
        assert c.status == c.status.STARTED
        env.stop()

    def test_dependency_failure(self, mocker):
        """
        With dep ``{(a, b): c}``, c depends on both a and b. b fails to
        start; a is independent and starts successfully in parallel.
        c must NOT be scheduled (status remains NONE).
        """
        m = mocker.Mock()
        env = TestEnvironment()
        a = FlakyDriver("a", m)
        b = FlakyDriver("b", m, pass_starting=False)
        c = FlakyDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({(a, b): c}))
        env.start()

        assert len(env.start_exceptions) == 1
        assert "While starting driver FlakyDriver[b]:" in str(
            list(env.start_exceptions.values())[0]
        )
        assert a.status == a.status.STARTED
        assert b.status == b.status.STARTING
        assert c.status == c.status.NONE
        env.stop()


class TestThreadedScheduling:
    def test_slow_driver_not_block_fast_peers_on_start(self, mocker):
        """
        With an empty dependency dict all drivers are scheduled at once.
        A slow driver A (long ``starting`` + long ``started_check``) must
        not block fast peers B and C: B and C should each have a short
        per-driver setup time, while A's setup time covers the full slow
        wait. Total ``env.start()`` wall time should also be on the
        order of A's wait, not the sum.
        """

        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver(
            "a", m, check_wait=1.0, total_start_wait=2, starting_wait=0.5
        )
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({}))

        t0 = time.time()
        env.start()
        elapsed = time.time() - t0

        assert a.status == a.status.STARTED
        assert b.status == b.status.STARTED
        assert c.status == c.status.STARTED

        # B and C must finish well before A
        a_setup = a.timer.last(key="setup").elapsed
        b_setup = b.timer.last(key="setup").elapsed
        c_setup = c.timer.last(key="setup").elapsed
        assert a_setup >= 2, f"A setup unexpectedly fast: {a_setup}s"
        assert b_setup < 0.5, f"B setup unexpectedly slow: {b_setup}s"
        assert c_setup < 0.5, f"C setup unexpectedly slow: {c_setup}s"

        # B and C must show as processed before A in the dep graph
        processed = env._rt_dependency.processed
        assert processed.index(id(b)) < processed.index(id(a))
        assert processed.index(id(c)) < processed.index(id(a))

        # Total wall time should be ~A's wait (parallel), not the sum
        assert elapsed < a_setup + 0.3, (
            f"env.start() took {elapsed}s, suggests serial scheduling"
        )
        env.stop()

    def test_slow_driver_not_block_fast_peers_on_stop(self, mocker):
        """
        Stop-side mirror of ``test_slow_driver_not_block_fast_peers``.
        A slow driver A on stop (long ``stopping`` + long
        ``stopped_check``) must not block fast peers B and C during
        ``env.stop()``.
        """
        m = mocker.Mock()
        env = TestEnvironment()
        a = MockDriver("a", m, stopping_wait=0.5, total_stop_wait=1.5)
        b = MockDriver("b", m)
        c = MockDriver("c", m)
        for d_ in [a, b, c]:
            env.add(d_)
        env.set_dependency(parse_dependency({}))
        env.start()

        t0 = time.time()
        env.stop()
        elapsed = time.time() - t0

        assert a.status == a.status.STOPPED
        assert b.status == b.status.STOPPED
        assert c.status == c.status.STOPPED

        a_teardown = a.timer.last(key="teardown").elapsed
        b_teardown = b.timer.last(key="teardown").elapsed
        c_teardown = c.timer.last(key="teardown").elapsed
        assert a_teardown >= 1.5, (
            f"A teardown unexpectedly fast: {a_teardown}s"
        )
        assert b_teardown < 0.5, f"B teardown unexpectedly slow: {b_teardown}s"
        assert c_teardown < 0.5, f"C teardown unexpectedly slow: {c_teardown}s"

        # B and C must show as processed before A in the (stop) dep graph
        processed = env._rt_dependency.processed
        assert processed.index(id(b)) < processed.index(id(a))
        assert processed.index(id(c)) < processed.index(id(a))

        # Total wall time should be ~A's teardown (parallel), not the sum
        assert elapsed < a_teardown + 0.3, (
            f"env.stop() took {elapsed}s, suggests serial teardown"
        )

    def test_pool_size_capping_with_late_joiner(self, mocker):
        """
        Patch ``MAX_WORKER_THREADS`` to 4 with five independent drivers
        a, b, c, d, e (a/c/d/e slow, b fast). The first scheduling round
        fills all 4 slots with a, b, c, d. b finishes quickly and frees
        a slot which e then takes; e runs alongside a, c, d for its own
        slow duration. Total elapsed should not be less than ~slow_a
        (the longest single window) and overall validates that the pool
        cap is honored (e cannot start in parallel with a from t=0).
        """
        mocker.patch("testplan.testing.environment.base.MAX_WORKER_THREADS", 4)
        m = mocker.Mock()
        slow, fast = 1.0, 0.2
        env = TestEnvironment()
        a = MockDriver("a", m, starting_wait=slow)
        b = MockDriver("b", m, starting_wait=fast)
        c = MockDriver("c", m, starting_wait=slow)
        d = MockDriver("d", m, starting_wait=slow)
        e = MockDriver("e", m, starting_wait=slow)
        for d_ in [a, b, c, d, e]:
            env.add(d_)
        env.set_dependency(parse_dependency({}))

        t0 = time.time()
        env.start()
        elapsed = time.time() - t0

        for drv in (a, b, c, d, e):
            assert drv.status == drv.status.STARTED

        a_setup = a.timer.last(key="setup").elapsed
        b_setup = b.timer.last(key="setup").elapsed
        e_setup = e.timer.last(key="setup").elapsed
        assert a_setup >= slow
        assert e_setup >= slow
        assert b_setup < slow, f"B setup unexpectedly slow: {b_setup}s"

        # e could not start at t=0 (pool was full with a/b/c/d); it had
        # to wait for b's slot to free. Validate that e started strictly
        # after b finished -- proves the pool cap is honored.
        b_ended = b.timer.last(key="setup").end
        e_started = e.timer.last(key="setup").start
        assert e_started >= b_ended, (
            f"e started at {e_started} but b ended at {b_ended}; "
            f"pool cap of 4 not enforced (e ran in parallel with all "
            f"4 initial drivers)"
        )

        # Once b's slot is reused by e, all 4 slow drivers run in
        # parallel within the pool, so total elapsed should be ~slow,
        # not 2*slow. Bound it tightly to confirm e was not serialized
        # behind a slow driver.
        assert elapsed < 2 * slow, (
            f"env.start() took {elapsed}s; expected < {2 * slow}s "
            f"(pool of 4 should let a/c/d/e run concurrently after b)"
        )
        assert elapsed >= slow + fast, (
            f"env.start() took {elapsed}s; expected >= {slow + fast}s "
            f"(at least b + e)"
        )
        env.stop()
