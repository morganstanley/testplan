"""
Place where we put a variety of higher-order stuffs.
"""


import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager, Generator, Union


@dataclass
class _Right:
    """
    Wrapper for value.

    Since right also means correct.
    """

    right: object


@dataclass
class _Left:
    """
    Wrapper for exception.

    What's left is not right.
    """

    left: Exception


class ComposedContextManager:
    """
    A composed context manager from list of context managers,
    with exception within some __enter__ bubbled out and
    exception inner the with block handled by context managers.
    """

    def __init__(self, head: ContextManager, *tail: ContextManager):
        self._inner = _compose_contexts(head, *tail)

    def __enter__(self):
        r = self._inner.__enter__()
        if isinstance(r, _Right):
            return r.right
        else:
            raise r.left

    def __exit__(self, exc_type, exc_value, traceback):
        return self._inner.__exit__(exc_type, exc_value, traceback)


@contextmanager
def _compose_contexts(
    head: ContextManager, *tail: ContextManager
) -> Generator[Union[_Left, _Right], None, None]:
    """
    Roll context managers together,
    entering from left to right,
    exiting from right to left.

    Since we use contextmanager decorator here, one yield must exist within
    each branch, thus we use an exception-value wrapper to pop out exceptions
    within __enter__.

    The return value of __exit__ should only matter when exception exists.
    If __exit__ return some truthy value, we know this current exception is
    caught.
    """

    if not tail:
        try:
            a = head.__enter__()
        except Exception as e:
            yield _Left(e)

        try:
            yield _Right(a)
        except:
            r = head.__exit__(*sys.exc_info())
            if r:
                return r
            else:
                raise
        else:
            head.__exit__(None, None, None)
    else:
        try:
            a = head.__enter__()
        except Exception as e:
            yield _Left(e)

        composed = _compose_contexts(*tail)
        b = composed.__enter__()
        try:
            if isinstance(b, _Left):
                yield b
            elif isinstance(b.right, tuple):
                yield _Right((a, *b.right))
            else:
                yield _Right((a, b.right))
        except:
            r = composed.__exit__(*sys.exc_info())
            if r:
                head.__exit__(None, None, None)
            else:
                r = head.__exit__(*sys.exc_info())
                if r:
                    return r
                else:
                    raise
        else:
            composed.__exit__(None, None, None)
            head.__exit__(None, None, None)


def compose_contexts(*args: ContextManager) -> ContextManager:
    return ComposedContextManager(*args)
