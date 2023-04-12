"""Basic local executor."""
import time
from typing import List

from .base import Executor
from testplan.report import TestGroupReport, Status, ReportCategories
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

    def _execute(self, uid: str) -> None:
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

        result = runnable.run()

        self._results[uid] = result

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
                        self._execute(next_uid)
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
                        self._results[next_uid] = result
                    finally:
                        self.ongoing.pop(0)

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

    def get_current_status_for_debug(self) -> List[str]:
        """
        Get current status of ``LocalRunner`` for debugging.

        :return: Status of ``LocalRunner``.
        :rtype: ``List[str]``
        """
        msgs = [f"{self.class_name} status: {self.status.tag}"]
        msgs.extend(super().get_current_status_for_debug())
        return msgs
