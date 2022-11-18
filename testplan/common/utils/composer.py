"""
Place where we put a variety of higher-order stuffs.
"""


from contextlib import ExitStack, contextmanager
from typing import Any, ContextManager, Generator


@contextmanager
def compose_contexts(
    head: ContextManager, *tail: ContextManager
) -> Generator[Any, None, None]:
    """
    Roll context managers together,
    entering from left to right,
    exiting from right to left.
    """
    with ExitStack() as stack:
        if len(tail):
            yield tuple(stack.enter_context(c) for c in [head, *tail])
        else:
            yield stack.enter_context(head)
