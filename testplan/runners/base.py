"""Executor base classes."""

import threading
import time
from collections import OrderedDict
from queue import Empty, Queue
from typing import Callable, Dict, Generator, List, Optional

from testplan.common.entity import Resource, ResourceConfig
from testplan.common.report.base import EventRecorder
from testplan.common.utils.thread import interruptible_join
from testplan.runnable.messaging import (
    InterExecutorMessage,
    InterExecutorMessageT,
    QueueChannels,
)


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

    Subclasses must implement the ``Executor._loop`` logic.
    """

    CONFIG = ExecutorConfig
    _STOP_TIMEOUT = 10

    def __init__(self, **options) -> None:
        super(Executor, self).__init__(**options)
        self._loop_handler = None
        self._input = OrderedDict()
        self._results = OrderedDict()
        self.ongoing = []

        # for cross-executor messaging
        # XXX: _msg_self_id is a workaround for inconsistent "uid"s
        self._msg_self_id: Optional[str] = None
        self._msg_in_channel: Optional[Queue] = None
        self._msg_out_channels: Optional[QueueChannels] = None
        self._msg_handlers: Dict[InterExecutorMessageT, Callable] = {
            InterExecutorMessageT.EXPECTED_ABORT: self._handle_expected_abort
        }
        self._msg_thread: Optional[threading.Thread] = None

    @property
    def class_name(self) -> str:
        """Returns the class name."""
        return self.__class__.__name__

    @property
    def results(self) -> OrderedDict:
        """Items results."""
        return self._results

    @property
    def added_items(self) -> OrderedDict:
        """Returns added items."""
        return self._input

    def added_item(self, uid: str) -> object:
        """Returns the added item."""
        return self._input[uid]

    # TODO: based on aborting logic it is not clear why any object is
    # a good item even if abort_entity swallows the AttributeError on missing
    # abort. Perhaps a bit more clarity is needed here?
    def add(self, item: object, uid: str) -> None:
        """
        Adds an item for execution.

        :param item: To be executed and create a result.
        :param uid: Unique id.
        """
        if self.active:
            self._input[uid] = item
            # `NoRunpathPool` adds item after calling `_prepopulate_runnables`
            # so the following step is still needed
            if uid not in self.ongoing:
                self.ongoing.append(uid)

    def get(self, uid: str) -> object:
        """Get item result by uid."""
        return self._results[uid]

    def _loop(self) -> None:
        raise NotImplementedError()

    def _msg_handling_loop(self) -> None:
        try:
            interval = self.cfg.active_loop_sleep
        except AttributeError:
            # FIXME
            self.logger.warning(
                "Config option ``active_loop_sleep`` not found in %s, "
                "will not start executor messaging loop.",
                self,
            )
            return

        while self.active and self.status.tag not in (
            self.status.STOPPING,
            self.status.STOPPED,
        ):
            try:
                msg: InterExecutorMessage = self._msg_in_channel.get_nowait()
            except Empty:
                pass
            else:
                self.logger.debug(
                    "Executor[%s] receiving %s.", self.uid(), msg.mark
                )
                self._msg_handlers[msg.mark](msg)
            time.sleep(interval)

    def _handle_expected_abort(self, _):
        raise NotImplementedError()

    def _prepopulate_runnables(self) -> None:
        # If we are to apply test_sorter, it would be here
        # but it's not easy to implement a reasonable behavior
        # as _input could be a mixture of runnable/task/callable
        self.ongoing = list(self._input.keys())

    def starting(self) -> None:
        """Starts the execution loop."""
        self._prepopulate_runnables()
        self._loop_handler = threading.Thread(target=self._loop)
        self._loop_handler.daemon = True
        self._loop_handler.start()

        if self._msg_self_id:
            self._msg_thread = threading.Thread(target=self._msg_handling_loop)
            self._msg_thread.daemon = True
            self._msg_thread.start()

    def stopping(self) -> None:
        """Stop the executor."""
        if self._loop_handler:
            interruptible_join(self._loop_handler, timeout=self._STOP_TIMEOUT)
        if self._msg_thread:
            interruptible_join(self._msg_thread, timeout=self._STOP_TIMEOUT)

    def abort_dependencies(self) -> Generator:
        """Abort items running before aborting self."""
        for uid in self.ongoing:
            yield self._input[uid]

    @property
    def is_alive(self) -> bool:
        """Poll the loop handler thread to check it is running as expected."""
        if self._loop_handler:
            return self._loop_handler.is_alive()
        else:
            return False

    def pending_work(self) -> bool:
        """Resource has pending work."""
        return len(self.ongoing) > 0

    def set_channel_specs(
        self, exec_mark: str, exec_chann: Queue, channels: QueueChannels
    ):
        self._msg_self_id = exec_mark
        self._msg_in_channel = exec_chann
        self._msg_out_channels = channels

    def get_current_status_for_debug(self) -> List[str]:
        """
        Gets information about items in ``Executor`` for debugging. Subclasses can override this method and
        implement a well suited method to get items current status.

        :return: Status of items in ``Executor``.
        """
        msgs = []
        if self.added_items:
            msgs.append(f"{self.class_name} {self.cfg.name} added items:")
            for item in self.added_items:
                msgs.append(f"\t{item}")
        else:
            msgs.append(f"No added items in {self.class_name}")

        if self.ongoing:
            msgs.append(f"{self.class_name} {self.cfg.name} pending items:")
            for item in self.ongoing:
                msgs.append(f"\t{item}")
        else:
            msgs.append(f"No pending items in {self.class_name}")

        return msgs
