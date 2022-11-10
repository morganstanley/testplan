"""Common utility modules."""

from contextlib import contextmanager


# TODO: typing, tests

@contextmanager
def compose_contexts(*args):
    """
    Roll context managers together, entering from left to right, exiting from right to left.
    """

    if not args:
        raise TypeError("compose_contexts: have nothing to compose")
    if len(args) == 1:
        with args[0] as a:
            yield a
    else:
        head, tail = args[0], args[1:]
        with head as a:
            with compose_contexts(*tail) as b:
                if isinstance(b, tuple):
                    yield (a, *b)
                else:
                    yield (a, b)
