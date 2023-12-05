"""Basic local executor."""
import threading
import time
from typing import List

import testplan.common.utils.selector as S
from testplan.report import ReportCategories, Status, TestGroupReport
from testplan.runnable.messaging import InterExecutorMessage
from testplan.runners.base import Executor
from testplan.runners.pools import tasks
from testplan.testing.base import Test, TestResult


class LocalRunner(Executor):
    """
    Basic local execution that inherits
    :py:class:`Executor <testplan.runners.base.Executor>`
    and accepts all
    :py:class:`ExecutorConfig <testplan.runners.base.ExecutorConfig>`
    options.
    """

    def __init__(self, **options) -> None:
        super(LocalRunner, self).__init__(**options)
        self._uid = "local_runner"
        self._to_abort = False
        self._curr_runnable_cv = threading.Condition()
        self._curr_runnable = None

    def execute(self, uid: str) -> TestResult:
        """Execute item implementation."""
        # First retrieve the input from its UID.
        target = self._input[uid]

        # Inspect the input type. Tasks must be materialized before
        # they can be run.
        if isinstance(target, Test):
            runnable = target
        elif isinstance(target, tasks.Task):
            runnable = target.materialize()
        elif callable(target):
            runnable = target()
        else:
            raise TypeError(f"Cannot execute target of type {type(target)}")

        # guard
        if not isinstance(runnable, Test):
            raise TypeError(f"Cannot execute target of type {type(runnable)}")
        # pass the ball
        if not runnable.parent:
            runnable.parent = self
        if not runnable.cfg.parent:
            runnable.cfg.parent = self.cfg

        with self._curr_runnable_cv:
            self._curr_runnable = runnable
            self._curr_runnable_cv.notify()
        result = self._curr_runnable.run()
        self._curr_runnable = None

        return result

    def _loop(self) -> None:
        """Execution loop implementation for local runner."""
        while self.active:
            if self.status == self.status.STARTING:
                self.status.change(self.status.STARTED)
            elif self.status == self.status.STARTED:
                try:
                    next_uid = self.ongoing[0]
                except IndexError:
                    pass
                else:
                    try:
                        result = self.execute(next_uid)
                    except Exception as exc:
                        result = TestResult()
                        result.report = TestGroupReport(
                            name=next_uid, category=ReportCategories.ERROR
                        )
                        result.report.status_override = Status.ERROR
                        result.report.logger.exception(
                            "Exception for %s on %s execution: %s",
                            next_uid,
                            self,
                            exc,
                        )
                    finally:
                        with self._curr_runnable_cv:
                            if not self._to_abort:
                                self._results[next_uid] = result
                                self.ongoing.pop(0)

                    if (
                        self.cfg.test_breaker_thres.plan_level
                        and result.report.status
                        <= self.cfg.test_breaker_thres.plan_level
                    ):
                        if self._msg_self_id is not None:
                            self._msg_out_channels.cast(
                                S.Not(S.Lit(self._msg_self_id)),
                                InterExecutorMessage.make_expected_abort(),
                            )
                        self._silently_skip_remaining()

            elif self.status == self.status.STOPPING:
                self.status.change(self.status.STOPPED)
                return
            time.sleep(self.cfg.active_loop_sleep)

    def starting(self) -> None:
        """Starting the local runner."""
        if self.parent:
            self._runpath = self.parent.runpath
        super(LocalRunner, self).starting()  # start the loop
        self.status.change(self.status.STARTED)  # Start is async

    def stopping(self) -> None:
        """Stopping the local runner."""
        super(LocalRunner, self).stopping()  # stop the loop
        self.status.change(self.status.STOPPED)  # Stop is async

    def aborting(self) -> None:
        """Aborting logic."""
        self.logger.critical("Discard pending tasks of %s.", self)
        # Will announce that all the ongoing tasks fail, but there is a buffer
        # period and some tasks might be finished, so, copy the uids of ongoing
        # tasks and set test result, although the report could be overwritten.
        ongoing = self.ongoing[:]
        while ongoing:
            uid = ongoing.pop(0)
            result = TestResult()
            result.report = TestGroupReport(
                name=uid, category=ReportCategories.ERROR
            )
            result.report.status_override = Status.ERROR
            result.report.logger.critical(
                "Test [%s] discarding due to %s abort.", uid, self.uid()
            )
            self._results[uid] = result

    def _silently_skip_remaining(self):
        self.ongoing = []

    def _handle_expected_abort(self, _):
        with self._curr_runnable_cv:
            if self._curr_runnable is None:
                if len(self.ongoing):
                    self._curr_runnable_cv.wait()
                    self._curr_runnable.abort()
            self._to_abort = True
            self._silently_skip_remaining()

    def get_current_status_for_debug(self) -> List[str]:
        """
        Get current status of ``LocalRunner`` for debugging.

        :return: Status of ``LocalRunner``.
        :rtype: ``List[str]``
        """
        msgs = [f"{self.class_name} status: {self.status.tag}"]
        msgs.extend(super().get_current_status_for_debug())
        return msgs
