"""Worker pool executor base classes."""
import datetime
import numbers
import os
import pprint
import queue
import threading
import time
import traceback
from typing import Optional, Tuple

from schema import And, Or

from testplan.common import entity
from testplan.common.config import ConfigOption
from testplan.common.utils import strings
from testplan.common.utils.path import change_directory, is_subdir, pwd
from testplan.common.utils.thread import interruptible_join
from testplan.common.utils.timing import wait_until_predicate
from testplan.report import ReportCategories
from testplan.runners.base import Executor, ExecutorConfig

from .communication import Message
from .connection import QueueClient, QueueServer
from .tasks import Task, TaskResult


class TaskQueue:
    """
    A priority queue that returns items in the order of priority small -> large.
    items with the same priority will be returned in the order they are added.
    """

    def __init__(self):
        self.q = queue.PriorityQueue()
        self.count = 0

    def put(self, priority, item):
        self.q.put((priority, self.count, item))
        self.count += 1

    def get(self):
        entry = self.q.get_nowait()
        return entry[0], entry[2]

    def __getattr__(self, name):
        return self.q.__getattribute__(name)


class WorkerConfig(entity.ResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.base.Worker` resource entity.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "index": Or(int, str),
            ConfigOption("transport", default=QueueClient): object,
            ConfigOption("restart_count", default=3): int,
        }


class WorkerBase(entity.Resource):
    """
    Worker resource that pulls tasks from the transport provided, executes them
    and sends back task results.

    :param index: Worker index id.
    :type index: ``int`` or ``str``
    :param transport: Transport class for pool/worker communication.
    :type transport: :py:class:`~testplan.runners.pools.connection.Client`
    :param restart_count: How many times a worker in pool can be restarted.
    :type restart_count: ``int``

    Also inherits all :py:class:`~testplan.common.entity.base.Resource`
    options.
    """

    CONFIG = WorkerConfig

    def __init__(self, **options):
        super().__init__(**options)
        self._metadata = None
        self._transport = self.cfg.transport()
        self.last_heartbeat = None
        self.assigned = set()
        self.requesting = 0
        self.restart_count = self.cfg.restart_count

    @property
    def transport(self):
        """Pool/Worker communication transport."""
        return self._transport

    @transport.setter
    def transport(self, transport):
        self._transport = transport

    @property
    def metadata(self):
        """Worker metadata information."""
        if not self._metadata:
            self._metadata = {
                "thread": threading.current_thread(),
                "index": self.cfg.index,
            }
        return self._metadata

    @property
    def outfile(self):
        """Stdout file."""
        return os.path.join(
            self.parent.runpath, "{}_startup".format(self.cfg.index)
        )

    def uid(self):
        """Worker unique index."""
        return self.cfg.index

    def respond(self, msg):
        """
        Method that the pool uses to respond with a message to the worker.

        :param msg: Response message.
        :type msg: :py:class:`~testplan.runners.pools.communication.Message`
        """
        self._transport.respond(msg)

    def rebase_attachment(self, result):
        """Rebase the path of attachment from remote to local"""
        pass

    def rebase_task_path(self, task):
        """Rebase the path of task from local to remote"""
        pass

    def __repr__(self):
        return "{}[{}]".format(self.__class__.__name__, self.cfg.index)


class Worker(WorkerBase):
    """
    Worker that runs a thread and pull tasks from transport
    """

    def __init__(self, **options):
        super().__init__(**options)
        self._handler = None

    @property
    def handler(self):
        return self._handler

    def starting(self):
        """Starts the daemonic worker loop."""
        self.make_runpath_dirs()
        self._handler = threading.Thread(
            target=self._loop, args=(self._transport,)
        )
        self._handler.daemon = True
        self._handler.start()

    def stopping(self):
        """Stops the worker."""
        if self._handler:
            interruptible_join(self._handler)
        self._handler = None

    def aborting(self):
        """Aborting logic, will not wait running tasks."""
        self._transport.disconnect()

    def _wait_started(self, timeout=None):
        """Ready to communicate with pool."""
        self.last_heartbeat = time.time()
        super(Worker, self)._wait_started(timeout=timeout)

    @property
    def is_alive(self):
        """Poll the loop handler thread to check it is running as expected."""
        return self._handler.is_alive()

    def _loop(self, transport):
        message = Message(**self.metadata)

        while self.active and self.status.tag not in (
            self.status.STOPPING,
            self.status.STOPPED,
        ):
            received = transport.send_and_receive(
                message.make(message.TaskPullRequest, data=1)
            )
            if received is None or received.cmd == Message.Stop:
                break
            elif received.cmd == Message.TaskSending:
                results = []
                for item in received.data:
                    results.append(self.execute(item))
                transport.send_and_receive(
                    message.make(message.TaskResults, data=results),
                    expect=message.Ack,
                )
            elif received.cmd == Message.Ack:
                pass
            time.sleep(self.cfg.active_loop_sleep)

    def execute(self, task):
        """
        Executes a task and return the associated task result.

        :param task: Task that worker pulled for execution.
        :type task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :return: Task result.
        :rtype: :py:class:`~testplan.runners.pools.tasks.base.TaskResult`
        """
        try:
            task_path = getattr(task, "_rebased_path")
            runnable = task.materialize()

            if isinstance(runnable, entity.Runnable):
                if not runnable.parent:
                    runnable.parent = self
                if not runnable.cfg.parent:
                    runnable.cfg.parent = self.cfg

            # for task discovery used with a monorepo project
            if task_path and not is_subdir(task_path, pwd()):
                with change_directory(os.path.abspath(task_path)):
                    result = runnable.run()
            else:
                result = runnable.run()

        except BaseException:
            task_result = TaskResult(
                task=task,
                result=None,
                status=False,
                reason=traceback.format_exc(),
            )
        else:
            task_result = TaskResult(task=task, result=result, status=True)

        return task_result


class PoolConfig(ExecutorConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.base.Pool` executor resource entity.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "name": str,
            ConfigOption("size", default=4): And(int, lambda x: x > 0),
            ConfigOption("worker_type", default=Worker): lambda x: issubclass(
                x, Worker
            ),
            ConfigOption("worker_heartbeat", default=None): Or(
                int, float, None
            ),
            ConfigOption("heartbeats_miss_limit", default=3): int,
            ConfigOption("restart_count", default=3): int,
            ConfigOption("max_active_loop_sleep", default=5): numbers.Number,
            ConfigOption("allow_task_rerun", default=True): bool,
        }


class Pool(Executor):
    """
    Pool task executor object that initializes workers and dispatches tasks.

    :param name: Pool name.
    :type name: ``str``
    :param size: Pool workers size. Default: 4
    :type size: ``int``
    :param worker_type: Type of worker to be initialized.
    :type worker_type: :py:class:`~testplan.runners.pools.base.Worker`
    :param worker_heartbeat: Worker heartbeat period.
    :type worker_heartbeat: ``int`` or ``float`` or ``NoneType``
    :param heartbeats_miss_limit: Maximum times a heartbeat is missed.
    :type heartbeats_miss_limit: ``int``
    :param restart_count: How many times a worker in pool can be restarted.
    :type restart_count: ``int``
    :param max_active_loop_sleep: Maximum value for delay logic in active sleep.
    :type max_active_loop_sleep: ``int`` or ``float``
    :param allow_task_rerun: Whether allow task to rerun when executing in this pool
    :type allow_task_rerun: ``bool``

    Also inherits all :py:class:`~testplan.runners.base.Executor` options.
    """

    CONFIG = PoolConfig
    CONN_MANAGER = QueueServer

    def __init__(
        self,
        name,
        size=4,
        worker_type=Worker,
        worker_heartbeat=None,
        heartbeats_miss_limit=3,
        restart_count=3,
        max_active_loop_sleep=5,
        allow_task_rerun=True,
        **options,
    ):
        options.update(self.filter_locals(locals()))
        super(Pool, self).__init__(**options)
        self.unassigned = TaskQueue()  # unassigned tasks
        self._executed_tests = []
        self._task_retries_cnt = {}  # uid: times_reassigned_without_result
        self._task_retries_limit = 2
        self._workers = entity.Environment(parent=self)
        self._workers_last_result = {}
        self._conn = self.CONN_MANAGER()
        self._conn.parent = self
        self._pool_lock = threading.Lock()
        self._metadata = None
        # Will set False when Pool is starting.
        self._exit_loop = True
        self._start_monitor_thread = True
        # Methods for handling different Message types. These are expected to
        # take the worker, request and response objects as the only required
        # positional args.
        self._request_handlers = {
            Message.ConfigRequest: self._handle_cfg_request,
            Message.TaskPullRequest: self._handle_taskpull_request,
            Message.TaskResults: self._handle_taskresults,
            Message.Heartbeat: self._handle_heartbeat,
            Message.SetupFailed: self._handle_setupfailed,
        }

    def uid(self):
        """Pool name."""
        return self.cfg.name

    def add(self, task, uid):
        """
        Add a task for execution.

        :param task: Task to be scheduled to workers.
        :type task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :param uid: Task uid.
        :type uid: ``str``
        """
        if not isinstance(task, Task):
            raise ValueError(
                "Task was expected, got {} instead.".format(type(task))
            )
        super(Pool, self).add(task, uid)
        self.unassigned.put(task.priority, uid)
        self._task_retries_cnt[uid] = 0

    def _can_assign_task(self, task):
        """
        Is this pool able to execute the task.

        :param task: Task to be scheduled to pool.
        :type task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :return: True if can assign task to pool, otherwise False
        :rtype: ``bool``
        """
        return True

    def _can_assign_task_to_worker(self, task, worker):
        """
        When a worker requests a task, it is necessary to verify that
        the worker is suitable to execute the task.

        :param task: Task to be scheduled to worker.
        :type task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :param worker: A worker created by pool executor.
        :type worker: :py:class:`~testplan.runners.pools.base.Worker`
        :return: True if can assign task to worker, otherwise False
        :rtype: ``bool``
        """
        return True

    def _loop(self):
        """
        Main executor work loop - runs in a separate thread when the Pool is
        started.
        """

        if self._start_monitor_thread:
            self.logger.debug("Starting worker monitor thread.")
            self._worker_monitor = threading.Thread(
                target=self._workers_monitoring
            )
            self._worker_monitor.daemon = True
            self._worker_monitor.start()

        while self.active and not self._exit_loop:
            msg = self._conn.accept()
            if msg:
                try:
                    self.handle_request(msg)
                except Exception:
                    self.logger.error(traceback.format_exc())

            time.sleep(self.cfg.active_loop_sleep)

    def handle_request(self, request: Message):
        """
        Handles a worker request. I.e TaskPull, TaskResults, Heartbeat etc.

        :param request: Worker request.
        :type request: :py:class:`~testplan.runners.pools.communication.Message`
        """

        sender_index = request.sender_metadata["index"]
        worker: Worker = self._workers[sender_index]

        self.logger.debug(
            "Pool %s received message from worker %s - %s, %s",
            self.cfg.name,
            worker,
            request.cmd,
            request.data,
        )

        if not worker.active:
            self.logger.warning(
                "Message from inactive worker %s - %s, %s",
                worker,
                request.cmd,
                request.data,
            )

        response = Message(**self._metadata)

        if not self.active or self.status == self.STATUS.STOPPING:
            worker.respond(response.make(Message.Stop))
        elif request.cmd in self._request_handlers:
            try:
                self._request_handlers[request.cmd](worker, request, response)
            except Exception:
                self.logger.error(traceback.format_exc())
                self.logger.debug(
                    "Not able to handle request from worker, sending Stop cmd"
                )
                worker.respond(response.make(Message.Stop))
        else:
            self.logger.error(
                "Unknown request: {} {} {} {}".format(
                    request, dir(request), request.cmd, request.data
                )
            )
            worker.respond(response.make(Message.Ack))

    def _handle_cfg_request(
        self, worker: Worker, _: Message, response: Message
    ):
        """Handle a ConfigRequest from a worker."""
        options = []
        cfg = self.cfg

        while cfg:
            options.append(cfg.denormalize())
            cfg = cfg.parent

        worker.respond(response.make(Message.ConfigSending, data=options))

    def _handle_taskpull_request(
        self, worker: Worker, request: Message, response: Message
    ):
        """Handle a TaskPullRequest from a worker."""
        tasks = []

        if self.status == self.status.STARTED:
            for _ in range(request.data):
                try:
                    priority, uid = self.unassigned.get()
                except queue.Empty:
                    break

                task = self._input[uid]
                worker.rebase_task_path(task)

                if self._can_assign_task(task):
                    if self._task_retries_cnt[uid] > self._task_retries_limit:
                        self._discard_task(
                            uid,
                            "{} already reached max retries limit: {}".format(
                                self._input[uid], self._task_retries_limit
                            ),
                        )
                        continue
                    else:
                        if self._can_assign_task_to_worker(task, worker):
                            self.logger.test_info(
                                "Scheduling {} to {}{}".format(
                                    task,
                                    worker,
                                    " (rerun {})".format(task.reassign_cnt)
                                    if task.reassign_cnt > 0
                                    else "",
                                )
                            )
                            worker.assigned.add(uid)
                            tasks.append(task)
                            task.executors.setdefault(self.cfg.name, set())
                            task.executors[self.cfg.name].add(worker.uid())
                            self.record_execution(uid)
                        else:
                            self.logger.test_info(
                                "Cannot schedule {} to {}".format(task, worker)
                            )
                            self.unassigned.put(task.priority, uid)
                            self._task_retries_cnt[uid] += 1
                else:
                    # Later may create a default local pool as failover option
                    self._discard_task(
                        uid,
                        "{} cannot be executed in {}".format(
                            self._input[uid], self
                        ),
                    )

            if tasks:
                worker.respond(response.make(Message.TaskSending, data=tasks))
                worker.requesting = request.data - len(tasks)
                return

        worker.requesting = request.data
        worker.respond(response.make(Message.Ack))

    def _handle_taskresults(
        self, worker: Worker, request: Message, response: Message
    ):
        """Handle a TaskResults message from a worker."""

        def task_should_rerun():
            if not self.cfg.allow_task_rerun:
                return False
            if not task_result.task:
                return False
            if task_result.task.rerun == 0:
                return False

            result = task_result.result
            if (
                task_result.status
                and result
                and result.run
                and result.report.passed
            ):
                return False

            if task_result.task.reassign_cnt >= task_result.task.rerun:
                self.logger.test_info(
                    "Will not rerun %(input)s again as it already "
                    "reached max rerun limit %(reruns)d",
                    {
                        "input": self._input[uid],
                        "reruns": task_result.task.rerun,
                    },
                )
                return False

            return True

        worker.respond(response.make(Message.Ack))
        for task_result in request.data:
            uid = task_result.task.uid()
            worker.assigned.remove(uid)
            self._workers_last_result.setdefault(worker, time.time())
            self.logger.test_info(
                "De-assign {} from {}".format(task_result.task, worker)
            )

            worker.rebase_attachment(task_result.result)

            if task_should_rerun():
                self.logger.test_info(
                    "Will rerun %(task)s for max %(rerun)d more times",
                    {
                        "task": task_result.task,
                        "rerun": task_result.task.rerun
                        - task_result.task.reassign_cnt,
                    },
                )
                self.unassigned.put(task_result.task.priority, uid)
                self._task_retries_cnt[uid] = 0
                self._input[uid].reassign_cnt += 1
                # Will rerun task, but still need to retain the result
                self._append_temporary_task_result(task_result)
                continue

            self._print_test_result(task_result)
            self._results[uid] = task_result
            self.ongoing.remove(uid)

    def _handle_heartbeat(
        self, worker: Worker, request: Message, response: Message
    ):
        """Handle a Heartbeat message received from a worker."""
        worker.last_heartbeat = time.time()
        self.logger.debug(
            f"Received heartbeat from {worker} at {request.data}"
            f" after {time.time() - request.data}s."
        )
        worker.respond(response.make(Message.Ack, data=worker.last_heartbeat))

    def _handle_setupfailed(
        self, worker: Worker, request: Message, response: Message
    ):
        """Handle a SetupFailed message received from a worker."""
        self.logger.test_info(
            "Worker %s setup failed:%s%s", worker, os.linesep, request.data
        )
        worker.respond(response.make(Message.Ack))
        self._decommission_worker(worker, "Aborting {}, setup failed.")

    def _decommission_worker(self, worker: Worker, message: str):
        """
        Decommission a worker by move all assigned task back to pool
        """
        self.logger.warning(message.format(worker))
        if os.path.exists(worker.outfile):
            self.logger.test_info("\tlogfile: %s", worker.outfile)
        while worker.assigned:
            uid = worker.assigned.pop()
            task = self._input[uid]
            self.logger.test_info(
                "Re-collect %s from %s to %s.", task, worker, self
            )
            self.unassigned.put(task.priority, uid)
            self._task_retries_cnt[uid] += 1

    def _workers_monitoring(self):
        """
        Worker fault tolerance logic. Check is based on:
        1) handler status
        2) heartbeat if available
        """
        previous_status = {
            "active": [],
            "inactive": [],
            "initializing": [],
            "abort": [],
        }
        loop_interval = self.cfg.worker_heartbeat or 5  # seconds
        break_outer_loop = False

        while self.active:
            hosts_status = {
                "active": [],
                "inactive": [],
                "initializing": [],
                "abort": [],
            }

            for worker in self._workers:
                status, reason = self._query_worker_status(worker)
                if status == "inactive":
                    with self._pool_lock:
                        if (
                            self.active
                            and self.status != self.status.STOPPING
                            and self.status != self.status.STOPPED
                        ):
                            if self._handle_inactive(worker, reason):
                                status = "active"
                        else:
                            self.logger.test_info(
                                "%s is aborting/stopping, exit monitor.", self
                            )
                            break_outer_loop = True
                            break

                hosts_status[status].append(worker)

            if break_outer_loop:
                break

            if hosts_status != previous_status:
                self.logger.info(
                    "Hosts status update at %s", datetime.datetime.now()
                )
                self.logger.info(pprint.pformat(hosts_status))
                previous_status = hosts_status

            if (
                not hosts_status["active"]
                and not hosts_status["initializing"]
                and not hosts_status["inactive"]
                and hosts_status["abort"]
            ):
                # all workers aborting / aborted
                if not self._exit_loop:
                    self.logger.critical(
                        "All workers are aborting / aborted, abort %s.", self
                    )
                    self.abort()  # TODO: abort pool in a monitor thread ?
                    break

            try:
                # For early finish of worker monitoring thread.
                wait_until_predicate(
                    lambda: not self.is_alive,
                    timeout=loop_interval,
                    interval=0.05,
                )
            except RuntimeError:
                self.logger.test_info("%s is not alive, exit monitor.", self)
                break

    def _query_worker_status(
        self, worker: Worker
    ) -> Tuple[str, Optional[str]]:
        """
        Query the current status of a worker. If heartbeat monitoring is
        enabled, check the last heartbeat time is within threshold.

        :param worker: Pool worker to query
        :return: worker status string - one of 'initializing', 'inactive' or
            'active', and an optional reason string
        """
        if not worker.active:
            return "abort", f"Worker {worker} aborting or aborted"

        if worker.status in (worker.status.STOPPING, worker.status.STOPPED):
            return "inactive", f"Worker {worker} stopping or stopped"

        if (
            worker.status == worker.status.NONE
            or worker.status == worker.status.STARTING
        ):
            return "initializing", None

        # else: worker must be in state STARTED
        if worker.status != worker.status.STARTED:
            raise RuntimeError(
                f"Worker in unexpected state {worker.status.tag}"
            )

        if not worker.is_alive:  # handler based monitoring
            return (
                "inactive",
                f"Decommission {worker}, handler no longer alive",
            )

        # If no heartbeat is configured, we treat the worker as "active"
        # since it is in state STARTED and its handler is alive.
        if not self.cfg.worker_heartbeat:
            return "active", None

        # else: do heartbeat based monitoring
        lag = time.time() - worker.last_heartbeat
        if lag > self.cfg.worker_heartbeat * self.cfg.heartbeats_miss_limit:
            return (
                "inactive",
                f"Has not been receiving heartbeat from {worker} for {lag} sec",
            )

        return "active", None

    def _handle_inactive(self, worker: Worker, reason: str) -> bool:
        """
        Handle an inactive worker.

        :param worker: worker object
        :type worker: :py:class:`~testplan.runners.pool.base.Worker`
        :param reason: why worker is considered inactive
        :type reason: ``str``
        :return: True if worker restarted, else False
        :rtype: ``bool``
        """
        if worker.status != worker.status.STARTED:
            return False

        self._decommission_worker(worker, reason)

        if worker.restart_count:
            worker.restart_count -= 1
            try:
                worker.restart()
                self.logger.info("Worker %s has restarted", worker)
                return True

            except Exception as exc:
                self.logger.critical(
                    "Worker %s failed to restart: %s", worker, exc
                )
        self.logger.warning("Worker %s is inactive and will abort", worker)
        worker.abort()

        return False

    def _discard_task(self, uid, reason: str):
        self.logger.critical(
            "Discard task %s of %s - %s", self._input[uid], self, reason
        )
        self._results[uid] = TaskResult(
            task=self._input[uid],
            status=False,
            reason=f"Task discarded by {self} - {reason}",
        )
        self.ongoing.remove(uid)

    def _discard_pending_tasks(self):
        self.logger.critical("Discard pending tasks of %s", self)
        while self.ongoing:
            uid = self.ongoing[0]
            target = self._input[uid]._target
            self._results[uid] = TaskResult(
                task=self._input[uid],
                status=False,
                reason=f"Task [{target}] discarding due to {self} abort",
            )
            self.ongoing.pop(0)

    def _append_temporary_task_result(self, task_result):
        """If a task should rerun, append the task result already fetched."""
        test_report = task_result.result.report
        uid = task_result.task.uid()
        if uid not in self._task_retries_cnt:
            return

        postfix = f" => Run {task_result.task.reassign_cnt}"
        test_report.name = f"{test_report.name}{postfix}"
        test_report.uid = f"{test_report.uid}{postfix}"
        test_report.category = ReportCategories.TASK_RERUN
        test_report.status_override = "xfail"
        new_uuid = strings.uuid4()
        self._results[new_uuid] = task_result
        self.parent._tests[new_uuid] = self.cfg.name
        self.record_execution(new_uuid)

    def _print_test_result(self, task_result):
        if (not isinstance(task_result.result, entity.RunnableResult)) or (
            not hasattr(task_result.result, "report")
        ):
            return

        # Currently prints report top level result and not details.
        name = task_result.result.report.name
        self.logger.log_test_status(name, task_result.result.report.status)

    def _add_workers(self):
        """Initialise worker instances."""
        for idx in (str(i) for i in range(self.cfg.size)):
            worker = self.cfg.worker_type(
                index=idx,
                restart_count=self.cfg.restart_count,
                active_loop_sleep=0.01,
            )
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=idx)

            self.logger.debug(
                "Added worker %(index)s (outfile = %(outfile)s)",
                {"index": idx, "outfile": worker.outfile},
            )

    def _start_workers(self):
        """Start all workers of the pool."""
        for worker in self._workers:
            self._conn.register(worker)
        self._workers.start()

    def _reset_workers(self):
        """
        Reset all workers in case that pool restarts but still use the existed
        workers. A worker in STOPPED status can make monitor think it is dead.
        """
        for worker in self._workers:
            worker.status.reset()

    def starting(self):
        """Starting the pool and workers."""
        # TODO do we need a lock here?
        self.make_runpath_dirs()
        if self.runpath is None:
            raise RuntimeError("runpath was not set correctly")
        self._metadata = {"runpath": self.runpath}

        self._conn.start()
        self._exit_loop = False
        if self._workers:
            self._reset_workers()

        super(Pool, self).starting()  # start the loop & monitor

        if not self._workers:
            self._add_workers()
        self._start_workers()

        if self._workers.start_exceptions:
            for msg in self._workers.start_exceptions.values():
                self.logger.error(msg)
            self.abort()
            raise RuntimeError(f"All workers of {self} failed to start")

    def workers_requests(self):
        """Count how many tasks workers are requesting."""
        return sum(worker.requesting for worker in self._workers)

    def _stop_workers(self):
        self._workers.stop()

    def stopping(self):
        """Stop connections and workers."""
        with self._pool_lock:
            self._stop_workers()
            for worker in self._workers:
                worker.transport.disconnect()

        self._exit_loop = True
        super(Pool, self).stopping()  # stop the loop (monitor will stop later)

        self._conn.stop()

    def abort_dependencies(self):
        """Empty generator to override parent implementation."""
        return
        yield

    def aborting(self):
        """Aborting logic."""
        for worker in self._workers:
            worker.abort()

        self._exit_loop = True
        super(Pool, self).stopping()  # stop the loop and the monitor

        self._conn.abort()
        self._discard_pending_tasks()

    def record_execution(self, uid):
        self._executed_tests.append(uid)
