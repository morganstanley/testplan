"""Basic local executor."""

import time

from .base import Executor
from testplan.runners.pools import tasks
from testplan.common import entity
from testplan.testing.base import TestResult
from testplan.report.testing import TestGroupReport, Status


class LocalRunner(Executor):
    """
    Basic local execution that inherits
    :py:class:`Executor <testplan.runners.base.Executor>`
    and accepts all
    :py:class:`ExecutorConfig <testplan.runners.base.ExecutorConfig>`
    options.
    """
    def __init__(self, **options):
        super(LocalRunner, self).__init__(**options)
        self._uid = 'local_runner'

    def _execute(self, uid):
        """Execute item implementation."""
        # First retrieve the input from its UID.
        target = self._input[uid]

        # Inspect the input type. Tasks must be materialized before they can be
        # run.
        if isinstance(target, tasks.Task):
            runnable = target.materialize()
            if not runnable.parent:
                runnable.parent = self
            if not runnable.cfg.parent:
                runnable.cfg.parent = self.cfg
        elif isinstance(target, entity.Runnable):
            runnable = target
        else:
            raise TypeError('Cannot execute target of type {}'
                            .format(type(target)))

        result = runnable.run()
        self._results[uid] = result

    def _loop(self):
        """Execution loop implementation for local runner."""
        while self.active:
            if self.status.tag == self.status.STARTING:
                self.status.change(self.status.STARTED)
            elif self.status.tag == self.status.STARTED:
                try:
                    next_uid = self.ongoing[0]
                except IndexError:
                    pass
                else:
                    try:
                        self._execute(next_uid)
                    except Exception as exc:
                        result = TestResult()
                        result.report = TestGroupReport(name=next_uid)
                        result.report.status_override = Status.ERROR
                        result.report.logger.exception(
                            'Exception for {} on {} execution: {}'.format(
                                next_uid, self, exc))
                        self._results[next_uid] = result
                    finally:
                        self.ongoing.pop(0)

            elif self.status.tag == self.status.STOPPING:
                self.status.change(self.status.STOPPED)
                return
            time.sleep(self.cfg.active_loop_sleep)

    def aborting(self):
        """Aborting logic."""
        self.logger.critical('Discard pending tasks of {}.'.format(self))
        # Will announce that all the ongoing tasks fail, but there is a buffer
        # period and some tasks might be finished, so, copy the uids of ongoing
        # tasks and set test result, although the report could be overwritten.
        ongoing = self.ongoing[:]
        while ongoing:
            uid = ongoing.pop(0)
            result = TestResult()
            result.report = TestGroupReport(name=uid)
            result.report.status_override = Status.ERROR
            result.report.logger.critical(
                'Test [{}] discarding due to {} abort.'.format(
                    uid, self.uid()))
            self._results[uid] = result

