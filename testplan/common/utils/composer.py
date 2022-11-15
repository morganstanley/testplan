"""
Place where we put a variety of higher-order stuffs.
"""


from types import TracebackType
from typing import ContextManager, Type


class ComposedContextManager:
    """
    Roll context managers together,
    entering from left to right,
    exiting from right to left.

    The return value of __exit__ should only matter when exception exists.
    If __exit__ return some truthy value, we know this current exception is
    caught.
    """

    def __init__(self, head: ContextManager, *tail: ContextManager):
        self.head = head
        self.tail = None
        if len(tail):
            self.tail = ComposedContextManager(*tail)

    def __enter__(self):
        r = self.head.__enter__()
        if self.tail is not None:
            rs = self.tail.__enter__()
            if isinstance(rs, tuple):
                return (r, *rs)
            else:
                return (r, rs)
        else:
            return r

    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ):
        if self.tail is not None:
            r = self.tail.__exit__(exc_type, exc_value, traceback)
            # If r is a truthy value, the exception is handled.
            if exc_type and not r:
                return self.head.__exit__(exc_type, exc_value, traceback)
            # We know self.tail.__exit__ has already handled the exception,
            # it's just the parameters are still not None here.
            self.head.__exit__(None, None, None)
            return True
        else:
            return self.head.__exit__(exc_type, exc_value, traceback)


def compose_contexts(
    head: ContextManager, *tail: ContextManager
) -> ContextManager:
    return ComposedContextManager(head, *tail)
