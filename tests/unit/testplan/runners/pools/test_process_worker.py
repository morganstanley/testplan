"""Unit test for process pool."""

import os
import platform
import psutil
import pytest
import time
from argparse import Namespace
from unittest import mock

import zmq

from testplan.common.serialization import deserialize, serialize
from testplan.common.utils import logger
from testplan.common.utils.timing import TimeoutException
from testplan.runners.pools import (
    child,
    communication,
    connection,
    process,
    tasks,
)
from testplan.runners.pools.base import Worker
from testplan.testing.common import SkipStrategy

logger.TESTPLAN_LOGGER.setLevel(logger.DEBUG)


@pytest.fixture
def starting_worker(tmp_path):
    worker = process.ProcessWorker(index="worker-0")
    worker.parent = mock.Mock(runpath=str(tmp_path))
    worker.status.change(worker.STATUS.STARTING)
    worker._handler = mock.Mock(returncode=17)
    worker._handler.poll.return_value = None
    worker.last_heartbeat = None
    worker._after_started = mock.Mock()
    return worker


def test_started_check_does_not_complete_lifecycle(starting_worker):
    worker = starting_worker
    with open(worker.outfile, "w") as logfile:
        logfile.write("Child is still initializing\n")
    assert not worker.started_check()
    with open(worker.outfile, "a") as logfile:
        logfile.write("Starting child process worker on host\n")
    assert worker.started_check()
    assert worker.status == worker.STATUS.STARTING
    assert worker.last_heartbeat is None
    worker._after_started.assert_not_called()


def test_blocking_wait_reuses_readiness_check(starting_worker):
    worker = starting_worker
    worker.started_check = mock.Mock(side_effect=[False, True])

    worker._wait_started(timeout=1)

    assert worker.started_check.call_count == 2
    worker._after_started.assert_called_once_with()
    assert worker.last_heartbeat is not None


@pytest.mark.parametrize("failure", ["timeout", "process_exit"])
def test_blocking_wait_failure(starting_worker, failure):
    worker = starting_worker
    with open(worker.outfile, "w") as logfile:
        logfile.write("Child is still initializing\n")
    if failure == "process_exit":
        worker._handler.poll.return_value = 17

    error = RuntimeError if failure == "process_exit" else TimeoutException
    message = (
        "process exited: 17"
        if failure == "process_exit"
        else "Worker start timeout"
    )
    with pytest.raises(error, match=message):
        worker._wait_started(timeout=0)

    worker._after_started.assert_not_called()
    assert worker.last_heartbeat is None


@pytest.mark.parametrize(
    "worker_type,pool_type,loop_name",
    [
        ("process_worker", "thread", "ChildLoop"),
        ("remote_worker", "thread", "RemoteChildLoop"),
        ("remote_worker", "process", "RemoteChildLoop"),
    ],
)
def test_child_response_timeout(worker_type, pool_type, loop_name):
    args = Namespace(
        address="127.0.0.1:12345",
        index="worker-1",
        log_level=logger.DEBUG,
        runpath=None,
        type=worker_type,
        remote_pool_type=pool_type,
        remote_pool_size=2,
        otel_traceparent="",
        otel_logs=False,
    )
    with (
        mock.patch.object(connection, "ZMQClient") as client,
        mock.patch.object(child, loop_name) as loop,
        mock.patch.object(logger, "TESTPLAN_LOGGER"),
    ):
        child.child_logic(args)

    client.assert_called_once_with(address=args.address, recv_timeout=60)
    assert loop.call_args.args[1] is client.return_value
    loop.return_value.worker_loop.assert_called_once_with()


@pytest.fixture
def proc_pool():
    pool = process.ProcessPool(
        name="ProcPool", size=2, restart_count=0, async_start=False
    )
    pool.cfg.set_local("skip_strategy", SkipStrategy.noop())
    return pool


class TestProcPool:
    """Tests for the ProcessPool class."""

    def test_run_task(self, proc_pool):
        """
        Test that a simple Task can be scheduled to a process pool and run.
        """
        # Create and add a basic example Task. When materialized and run,
        # the Runnable will return the product of its args: 7 * 3 => 21.
        example_task = tasks.Task(
            target="Runnable",
            module="tests.unit.testplan.runners.pools.tasks.data.sample_tasks",
            args=(7, 3),
        )
        proc_pool.add(example_task, example_task.uid())
        with proc_pool:
            assert proc_pool.status == proc_pool.status.STARTED
            while proc_pool.pending_work():
                assert proc_pool.is_alive
                time.sleep(0.2)

        assert proc_pool.status == proc_pool.status.STOPPED

        # Check that the expected result is stored both on the worker and
        # on the pool's result.
        assert proc_pool.get(example_task.uid()).result.report.val == 21
        assert proc_pool.results[example_task.uid()].result.report.val == 21

    def test_add_main(self, proc_pool):
        """
        Test scheduling a Task from the __main__ module. This should not be
        allowed, since __main__ is a different module for the child process.
        """
        main_task = tasks.Task(target="runnable", module="__main__")
        with pytest.raises(ValueError):
            proc_pool.add(main_task, main_task.uid())

    def test_start_stop(self, proc_pool):
        """Test basic start/stop of ProcessPool."""
        # This testcase is known to fail on Windows - mark as xfail until we
        # can fix it up.
        if platform.system() == "Windows":
            pytest.xfail("ProcPool start/stop is unstable on Windows")

        current_proc = psutil.Process()
        start_children = current_proc.children()

        # Iterate 5 times to increase the chance of hitting a race condition.
        for _ in range(5):
            with proc_pool:
                assert proc_pool.status == proc_pool.status.STARTED
                assert len(current_proc.children()) == len(start_children) + 2

            assert proc_pool.status == proc_pool.status.STOPPED
            assert len(current_proc.children()) == len(start_children)


def test_pool_zmq_heartbeat_from_inactive_worker():
    """
    Heartbeat from a disconnected worker gets Stop, REP stays unwedged
    for a second cycle.
    """

    class StubWorker(process.ProcessWorker):
        def starting(self):
            self.status.change(self.STATUS.STARTED)

        def stopping(self):
            self.status.change(self.STATUS.STOPPED)

        def aborting(self):
            self._transport.disconnect()

        def _wait_started(self, timeout=None):
            # Skip ProcessWorker's logfile poll — there's no subprocess.
            Worker._wait_started(self, timeout=timeout)

        @property
        def is_alive(self):
            return self.status.tag == self.STATUS.STARTED

    pool = process.ProcessPool(
        name="ZMQHBPool",
        size=1,
        worker_type=StubWorker,
        worker_heartbeat=None,
        async_start=False,
    )
    pool.cfg.set_local("skip_strategy", SkipStrategy.noop())
    pool._start_monitor_thread = False

    with pool:
        worker = pool._workers["0"]

        ctx = zmq.Context()
        req = ctx.socket(zmq.REQ)
        req.RCVTIMEO = 2000
        req.connect(f"tcp://{pool._conn.address}")
        try:
            worker._should_abort = True
            worker.transport.disconnect()
            assert not worker.active
            assert not worker.transport.active

            msg_factory = communication.Message(
                index=worker.cfg.index, pid=os.getpid()
            )

            req.send(
                serialize(
                    msg_factory.make(
                        communication.Message.Heartbeat, data=time.time()
                    )
                )
            )
            assert deserialize(req.recv()).cmd == communication.Message.Stop

            # Second cycle: REP must still be usable.
            req.send(
                serialize(
                    msg_factory.make(
                        communication.Message.Heartbeat, data=time.time()
                    )
                )
            )
            assert deserialize(req.recv()).cmd == communication.Message.Stop
        finally:
            req.close()
            ctx.destroy()
