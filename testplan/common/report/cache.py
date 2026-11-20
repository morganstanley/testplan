"""
Short-lived cache for the report properties that walk the tree.

``status``, ``counter`` and ``hash`` read their children, and a dump
reads each of them for every node, so one dump repeats the same walk
many times. :py:func:`report_cache` holds the results for a block in
which the report does not change.

The cache stays off until a caller opens it. It lives outside the
report, so no copy and no pickle of a report carries a value.
"""

import contextvars
import functools
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

_CACHE: contextvars.ContextVar[
    Optional[Dict[Tuple[str, int], Tuple[Any, Any]]]
] = contextvars.ContextVar("report_cache", default=None)


@contextmanager
def report_cache() -> Iterator[None]:
    """
    Hold the values of the cached report properties.

    The report must not change inside the block. The cache keeps
    each node it sees alive, so an ``id()`` is never reused.
    """
    token = _CACHE.set({})
    try:
        yield
    finally:
        _CACHE.reset(token)


def cached(func: Callable) -> Callable:
    """
    Memo a report property inside a `report_cache` block.

    The caller gets the stored object, not a copy. Do not change it.
    """
    name = func.__name__

    @functools.wraps(func)
    def wrapper(self: Any) -> Any:
        cache = _CACHE.get()
        if cache is None:
            return func(self)
        key = (name, id(self))
        try:
            return cache[key][1]
        except KeyError:
            value = func(self)
            # Hold self, so its id stays unique
            cache[key] = (self, value)
            return value

    return wrapper
