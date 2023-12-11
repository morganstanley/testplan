from dataclasses import dataclass
from enum import IntEnum, auto
from queue import Queue
from typing import Any, Dict, Tuple

from testplan.common.utils.selector import Expr, apply_on_set


class InterExecutorMessageT(IntEnum):
    EXPECTED_ABORT = auto()


@dataclass
class InterExecutorMessage:
    # NOTE: no src/dst fields here, need them?
    mark: InterExecutorMessageT
    data: Any

    @classmethod
    def make_expected_abort(cls):
        return cls(InterExecutorMessageT.EXPECTED_ABORT, None)


class QueueChannels:
    def __init__(self):
        self._qes: Dict[str, Queue] = {}

    def new_channel(self, name: str) -> Tuple[str, Queue]:
        self._qes[name] = Queue()
        # XXX: this return type is a workaround for non-u uids, might be refactored
        # XXX: in the future
        return name, self._qes[name]

    def cast(self, selector: Expr, msg: InterExecutorMessageT):
        for k in apply_on_set(selector, set(self._qes.keys())):
            self._qes[k].put(msg)
