"""TODO."""

import os
import random

from testplan import Task
from testplan.common.utils.path import default_runpath
from testplan.runners.pools import base as pools_base
from testplan.runners.pools import communication
from testplan.runners.pools.base import TaskQueue
from tests.unit.testplan.runners.pools.tasks.data.sample_tasks import Runnable


def test_task_queue():
    task_queue = TaskQueue()
    uids = [
        "abc",
        "def",
        "xyz",
    ]
    random.shuffle(uids)

    for uid in uids:
        for priority in [3, 2, 1]:
            task_queue.put(priority, uid)

    for priority in [1, 2, 3]:
        for uid in uids:
            assert task_queue.get() == (priority, uid)


def test_pool_basic():
    dirname = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dirname, "tasks", "data", "relative")

    task1 = Task(target=Runnable(5))
    task2 = Task(
        target="Runnable",
        module="sample_tasks",
        path=path,
        args=(10,),
        kwargs=dict(multiplier=3),
    )

    assert task1.materialize().run().report.val == 10
    assert task2.materialize().run().report.val == 30

    pool = pools_base.Pool(
        name="MyPool", size=4, runpath=default_runpath, allow_task_rerun=False
    )
    pool.add(task1, uid=task1.uid())
    pool.add(task2, uid=task2.uid())
    assert pool._input[task1.uid()] is task1
    assert pool._input[task2.uid()] is task2

    with pool:
        while pool.ongoing:
            pass

    assert (
        pool.get(task1.uid()).result.report.val
        == pool.results[task1.uid()].result.report.val
        == 10
    )
    assert (
        pool.get(task2.uid()).result.report.val
        == pool.results[task2.uid()].result.report.val
        == 30
    )


class ControllableWorker(pools_base.Worker):
    """
    Custom worker tweaked to give the testbed fine-grained control of messages
    sent to the pool.
    """

    def __init__(self, **kwargs):
        self._is_alive = False
        self._restart_count = 0
        super(ControllableWorker, self).__init__(**kwargs)

    def starting(self):
        """Override starting() so that no work loop is started."""
        self._is_alive = True
        self.status.change(self.STATUS.STARTED)

    def stopping(self):
        """
        Override stopping() so that it doesn't attempt to stop the work loop.
        """
        self._is_alive = False
        self.status.change(self.STATUS.STOPPED)

    def restart(self):
        self._restart_count += 1
        self._is_alive = True

    @property
    def is_alive(self):
        """We control whether the Worker is alive."""
        return self._is_alive


class TestPoolIsolated:
    """
    Test the Pool class in isolation, using a custom testbed worker that allows
    us to send in individual worker requests and check their responses.
    """

    def test_mainline(self):
        """
        Test mainline message flow between a worker and its Pool. The worker
        polls for a task and when one is received, the worker sends back the
        results of executing that task.
        """
        pool = pools_base.Pool(
            name="MyPool", size=1, worker_type=ControllableWorker
        )

        # Start the pool via its context manager - this starts the Pool's main
        # work loop in a separate thread.
        with pool:
            assert pool.is_alive and pool.active
            assert pool.status == pool.status.STARTED

            # Retrieve the only worker assigned to this pool.
            assert len(pool._workers) == 1
            worker = pool._workers["0"]
            assert worker.is_alive and worker.active
            assert worker.status == worker.status.STARTED

            msg_factory = communication.Message(**worker.metadata)

            # Send a TaskPullRequest from the worker to the Pool. The Pool
            # should respond with an Ack since no Tasks have been added yet.
            received = worker.transport.send_and_receive(
                msg_factory.make(msg_factory.TaskPullRequest, data=1)
            )
            assert received.cmd == communication.Message.Ack

            # Add a task to the pool.
            task1 = Task(target=Runnable(5))
            pool.add(task1, uid=task1.uid())

            # Send in another TaskPullRequest - the Pool should respond with
            # the task we just added.
            received = worker.transport.send_and_receive(
                msg_factory.make(msg_factory.TaskPullRequest, data=1)
            )
            assert received.cmd == communication.Message.TaskSending
            assert len(received.data) == 1
            assert received.data[0] == task1

            # Execute the task and send back the TaskResults.
            task_result = worker.execute(task1)
            results = [task_result]
            received = worker.transport.send_and_receive(
                msg_factory.make(msg_factory.TaskResults, data=results)
            )
            assert received.cmd == communication.Message.Ack

            # Check that the pool now has the results stored.
            assert pool._results[task1.uid()] == task_result

        # The Pool and its work loop should be stopped on exiting the context
        # manager.
        assert pool.status == pool.status.STOPPED

    def test_restart_worker_inactive(self):
        pool = pools_base.Pool(
            name="MyPool", size=1, worker_type=ControllableWorker
        )
        pool._start_monitor_thread = False

        with pool:

            worker = pool._workers["0"]
            assert pool._query_worker_status(worker) == ("active", None)

            worker._is_alive = False
            assert pool._query_worker_status(worker) == (
                "inactive",
                "Decommission {}, handler no longer alive".format(worker),
            )

            assert pool._handle_inactive(worker, "test restart") == True
            assert worker._restart_count == 1

    def test_restart_pool_stopping(self):

        pool = pools_base.Pool(
            name="MyPool", size=1, worker_type=ControllableWorker
        )
        pool._start_monitor_thread = False

        with pool:
            worker = pool._workers["0"]

        assert worker._restart_count == 0
