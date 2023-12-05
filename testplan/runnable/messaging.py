from dataclasses import dataclass
from enum import IntEnum, auto
from queue import Queue
from typing import Any, Dict, Tuple

from testplan.common.utils.selector import SExpr


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


# shortcuts
InterExecutorMessage.STOP = InterExecutorMessageT.EXPECTED_ABORT


class QueueChannels:
    def __init__(self):
        self._qes: Dict[str, Queue] = {}

    def new_channel(self, name: str) -> Tuple[str, Queue]:
        self._qes[name] = Queue()
        # XXX: this return type is a workaround for non-u uids, might be refactored
        # XXX: in the future
        return name, self._qes[name]

    def cast(self, selector: SExpr, msg: InterExecutorMessageT):
        for k, q in self._qes.items():
            if selector.eval(k):
                q.put(msg)
