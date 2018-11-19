"""Basic local executor."""

import time

from .base import Executor
from testplan.runners.pools import tasks
from testplan.common import entity


class LocalRunner(Executor):
    """
    Basic local execution that inherits
    :py:class:`Executor <testplan.runners.base.Executor>`
    and accepts all
    :py:class:`ExecutorConfig <testplan.runners.base.ExecutorConfig>`
    options.
    """

    def _execute(self, uid):
        """Execute item implementation."""
        # First retrieve the input from its UID.
        target = self._input[uid]

        # Inspect the input type. Tasks must be materialized before they can be
        # run.
        if isinstance(target, tasks.Task):
            runnable = target.materialize()
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
                    self._execute(next_uid)
                    self.ongoing.pop(0)

            elif self.status.tag == self.status.STOPPING:
                self.status.change(self.status.STOPPED)
                return
            time.sleep(self.cfg.active_loop_sleep)

    def aborting(self):
        """Suppressing not implemented debug log from parent class."""

