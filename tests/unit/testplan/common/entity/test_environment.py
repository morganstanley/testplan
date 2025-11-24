import multiprocessing.pool as mp
import os
import sys
import time

import pytest

from testplan.common.entity.base import Environment, Resource

# Python 3.13+ uses process_cpu_count() for ThreadPool sizing
if sys.version_info >= (3, 13):
    CPU_COUNT = os.process_cpu_count() or 1
else:
    CPU_COUNT = os.cpu_count() or 1


@pytest.fixture
def environment():
    return Environment()


@pytest.fixture
def pool():
    return mp.ThreadPool(CPU_COUNT)


class DummyResource(Resource):
    def __init__(
        self,
        starting=None,
        stopping=None,
        wait_started=None,
        wait_stopped=None,
        **options,
    ):
        # other ops should exist in cfg
        super().__init__(**options)
        self._c_starting = starting or (lambda: None)
        self._c_stopping = stopping or (lambda: None)
        self._c_wait_started = wait_started or (lambda: None)
        self._c_wait_stopped = wait_stopped or (lambda: None)

    def starting(self):
        self._c_starting()

    def stopping(self):
        self._c_stopping()

    def _wait_started(self, timeout=None):
        self._c_wait_started()
        super()._wait_started(timeout)

    def _wait_stopped(self, timeout=None):
        self._c_wait_stopped()
        super()._wait_stopped(timeout)


class TestConcurrentResourceOps:
    def test_basic(self, environment, pool, mocker):
        pre, post = mocker.Mock(), mocker.Mock()
        environment.add(
            DummyResource(
                pre_start=pre,
                wait_started=lambda: time.sleep(1),
                post_start=post,
                pre_stop=pre,
                wait_stopped=lambda: time.sleep(1),
                post_stop=post,
            )
        )
        environment.add(
            DummyResource(
                pre_start=pre,
                wait_started=lambda: time.sleep(1),
                post_start=post,
                pre_stop=pre,
                wait_stopped=lambda: time.sleep(1),
                post_stop=post,
            )
        )
        a = time.time()
        environment.start_in_pool(pool)
        b = time.time()

        if CPU_COUNT >= 2:
            assert b - a < 2, "resources didn't start concurrently"
        assert pre.call_count == 2, "pre-hooks not invoked"
        assert post.call_count == 2, "post-hooks not invoked"

        c = time.time()
        environment.stop_in_pool(pool)
        d = time.time()

        if CPU_COUNT >= 2:
            assert d - c < 2, "resources didn't stop concurrently"
        assert pre.call_count == 4, "pre-hooks not invoked"
        assert post.call_count == 4, "post-hooks not invoked"

    def test_long_pre(self, environment, pool, mocker):
        wait, post = mocker.Mock(), mocker.Mock()
        environment.add(
            DummyResource(
                pre_start=lambda _: time.sleep(1.5),
                wait_started=wait,
                post_start=post,
                status_wait_timeout=1,
            )
        )
        environment.add(
            DummyResource(
                pre_start=lambda _: time.sleep(1.5),
                wait_started=wait,
                post_start=post,
                status_wait_timeout=1,
            )
        )
        a = time.time()
        environment.start_in_pool(pool)
        b = time.time()
        environment.stop_in_pool(pool)

        if CPU_COUNT >= 2:
            assert b - a < 3, "resources didn't start concurrently"
        assert wait.call_count == 2, "wait-hooks not invoked"
        assert post.call_count == 2, "post-hooks not invoked"

    def test_long_post(self, environment, pool, mocker):
        wait, pre = mocker.Mock(), mocker.Mock()
        environment.add(
            DummyResource(
                post_stop=lambda _: time.sleep(1.5),
                wait_stopped=wait,
                pre_stop=pre,
                status_wait_timeout=1,
            )
        )
        environment.add(
            DummyResource(
                post_stop=lambda _: time.sleep(1.5),
                wait_stopped=wait,
                pre_stop=pre,
                status_wait_timeout=1,
            )
        )
        environment.start_in_pool(pool)
        a = time.time()
        environment.stop_in_pool(pool)
        b = time.time()

        if CPU_COUNT >= 2:
            assert b - a < 3, "resources didn't stop concurrently"
        assert wait.call_count == 2, "wait-hooks not invoked"
        assert pre.call_count == 2, "pre-hooks not invoked"

    def test_manual_resource(self, environment, pool, mocker):
        pre, wait, post = mocker.Mock(), mocker.Mock(), mocker.Mock()
        m = DummyResource(
            pre_start=pre,
            wait_started=wait,
            post_start=post,
            pre_stop=pre,
            wait_stopped=wait,
            post_stop=post,
            auto_start=False,
        )
        environment.add(m)
        environment.add(
            DummyResource(
                pre_start=lambda _: time.sleep(1),
            )
        )
        environment.add(
            DummyResource(
                post_start=lambda _: time.sleep(1),
            )
        )
        a = time.time()
        environment.start_in_pool(pool)
        b = time.time()
        if CPU_COUNT >= 2:
            assert b - a < 2, "resources didn't start concurrently"
        assert not len(environment.start_exceptions)

        m.start()
        m.wait(m.STATUS.STARTED)
        m.stop()
        m.wait(m.STATUS.STOPPED)

        assert pre.call_count == 2, "pre-hooks not invoked"
        assert wait.call_count == 2, "wait-hooks not invoked"
        assert post.call_count == 2, "post-hooks not invoked"

        environment.stop_in_pool(pool)
        assert not len(environment.stop_exceptions)

    def test_op_timeout(self, environment, pool, mocker):
        environment.add(
            DummyResource(
                pre_stop=lambda _: time.sleep(2),
            )
        )
        environment.add(
            DummyResource(
                pre_start=lambda _: time.sleep(2),
            )
        )
        with pytest.raises(
            RuntimeError, match="timeout after 0.2s when starting"
        ):
            environment.start_in_pool(pool, timeout=0.2)
        with pytest.raises(
            RuntimeError, match="timeout after 0.2s when stopping"
        ):
            environment.stop_in_pool(pool, timeout=0.2)

    def test_nested_pool(self, mocker):
        wait, post = mocker.Mock(), mocker.Mock()
        with mp.ThreadPool(CPU_COUNT) as another_pool:

            def _nested(_):
                environment = Environment()
                pool = mp.ThreadPool(CPU_COUNT)
                environment.add(
                    DummyResource(
                        pre_stop=lambda _: time.sleep(1),
                        wait_stopped=wait,
                        post_stop=post,
                    )
                )
                environment.add(
                    DummyResource(
                        pre_stop=lambda _: time.sleep(1),
                        wait_stopped=wait,
                        post_stop=post,
                    )
                )
                environment.start_in_pool(pool)
                a = time.time()
                environment.stop_in_pool(pool)
                b = time.time()

                if CPU_COUNT >= 4:
                    assert b - a < 4, "resources didn't start concurrently"

            r = another_pool.map_async(
                _nested,
                [None, None],
            )
            assert r.get() == [None, None], "nested pool execution failed"
            assert wait.call_count == 4, "wait-hooks not invoked"
            assert post.call_count == 4, "post-hooks not invoked"
