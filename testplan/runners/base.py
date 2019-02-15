"""Executor base classes."""

import threading

from collections import OrderedDict

from testplan.common.entity import Resource, ResourceConfig
from testplan.common.utils.thread import interruptible_join


class ExecutorConfig(ResourceConfig):
    """
    Configuration object for
    :py:class:`Executor <testplan.runners.base.Executor>` resource.

    Inherits all
    :py:class:`~testplan.common.entity.base.ResourceConfig`
    options.
    """


class Executor(Resource):
    """
    Receives items, executes them and create results.

    Subclasses must implement the ``Executor._loop`` and
    ``Executor._execute`` logic to execute the input items.
    """

    CONFIG = ExecutorConfig

    def __init__(self, **options):
        super(Executor, self).__init__(**options)
        self._loop_handler = None
        self._input = OrderedDict()
        self._results = OrderedDict()
        self.ongoing = []

    @property
    def results(self):
        """Items results."""
        return self._results

    @property
    def added_items(self):
        """Returns added items."""
        return self._input

    def added_item(self, uid):
        """Returns the added item."""
        return self._input[uid]

    def add(self, item, uid):
        """
        Adds an item for execution.

        :param item: To be executed and create a result.
        :type item: ``object``
        :param uid: Unique id.
        :type uid: ``str``
        """
        if self.active:
            self._input[uid] = item
            self.ongoing.append(uid)

    def get(self, uid):
        """Get item result by uid."""
        return self._results[uid]

    def _loop(self):
        raise NotImplementedError()

    def _execute(self, uid):
        raise NotImplementedError()

    def _prepopulate_runnables(self):
        self.ongoing = list(self._input.keys())

    def starting(self):
        """Starts the execution loop."""
        self._prepopulate_runnables()
        self._loop_handler = threading.Thread(target=self._loop)
        self._loop_handler.daemon = True
        self._loop_handler.start()

    def stopping(self):
        """Stop the executor."""
        if self._loop_handler:
            interruptible_join(self._loop_handler)

    def abort_dependencies(self):
        """Abort items running before aborting self."""
        for uid in self.ongoing:
            yield self._input[uid]

    @property
    def is_alive(self):
        """Poll the loop handler thread to check it is running as expected."""
        return self._loop_handler.is_alive()

    def pending_work(self):
        """Resource has pending work."""
        return len(self.ongoing) > 0