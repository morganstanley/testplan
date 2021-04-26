"""Utilities related to python callables (functions, methods, classes etc.)"""

import inspect
import functools
from collections import namedtuple


WRAPPER_ASSIGNMENTS = functools.WRAPPER_ASSIGNMENTS + (
    "__tags__",
    "__tags_index__",
    "wrapper_of",
    "summarize",
    "summarize_num_passing",
    "summarize_num_failing",
)

# Local copy of inspect.ArgSpec namedtuple - see notes on inspect.getargspec()
# deprecation within getargspec() below.
ArgSpec = namedtuple("ArgSpec", ["args", "varargs", "keywords", "defaults"])


def arity(function):
    """
    Return the arity of a function

    :param function: function
    :type function: ``function``

    :return: arity of the function
    :rtype: ``int``
    """
    return len(getargspec(function).args)


def getargspec(callable_):
    """
    Return an Argspec for any callable object

    :param callable_: a callable object
    :type callable_: ``Callable``

    :return: argspec for the callable
    :rtype: ``ArgSpec``
    """
    if not callable(callable_):
        raise ValueError("{} is not callable".format(callable_))

    if inspect.ismethod(callable_) or inspect.isfunction(callable_):
        func = callable_
    else:
        func = callable_.__call__

    # In Python 3.7 inspect.getargspec() is deprecated and will be removed in
    # 3.8, due to the addition of keyword-only args and type annotations
    # (see PEPs 3102 and 484 for more information). To retain backwards
    # compatibility we convert from a FullArgSpec to a python2 ArgSpec.
    full_argspec = inspect.getfullargspec(func)

    # Raise a ValueError if the function has any keyword-only args defined,
    # since we can't easily handle them in a way that is also python 2
    # compatible. On the other hand, we can just discard any information on
    # type annotations.
    if full_argspec.kwonlyargs:
        raise ValueError(
            "Cannot get argspec for function with keyword-only args "
            "defined: {}".format(func)
        )
    return ArgSpec(
        args=full_argspec.args,
        varargs=full_argspec.varargs,
        keywords=full_argspec.varkw,
        defaults=full_argspec.defaults,
    )


# backport from python 3.6, 2.7 version does not catch AttributeError
def update_wrapper(
    wrapper,
    wrapped,
    assigned=WRAPPER_ASSIGNMENTS,
    updated=functools.WRAPPER_UPDATES,
):
    """
    Update a wrapper function to look like the wrapped function.

    :param wrapper: Function to be updated.
    :type wrapper: ``func``
    :param wrapped: Original function.
    :type wrapped: ``func``
    :param assigned: Tuple naming the attributes assigned directly from the
                     wrapped function to the wrapper function (defaults to
                     functools.WRAPPER_ASSIGNMENTS)
    :type assigned: ``tuple``
    :param updated: tuple naming the attributes of the wrapper that are updated
                    with the corresponding attribute from the wrapped function
                    (defaults to functools.WRAPPER_UPDATES)
    :type updated: ``tuple``
    :return: Wrapper function.
    :rtype: ``func``
    """
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)
    for attr in updated:
        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
    # Issue #17482: set __wrapped__ last so we don't inadvertently copy it
    # from the wrapped function when updating __dict__
    wrapper.__wrapped__ = wrapped
    # Return the wrapper so this can be used as a decorator via partial()
    return wrapper


def wraps(
    wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=functools.WRAPPER_UPDATES
):
    """
    Custom wraps function that uses the backported ``update_wrapper``.

    Also sets ``wrapper_of`` attribute for code highlighting, for methods that
    are decorated for the first time.
    """

    def _inner(wrapper):
        wrapper = update_wrapper(
            wrapper=wrapper,
            wrapped=wrapped,
            assigned=assigned,
            updated=updated,
        )

        # When a method is decorated for the first time it will not have
        # `wrapper_of` attribute set, so `update_wrapper` won't be able to copy
        # it over. That's why we have to explicitly assign it here.
        if not hasattr(wrapped, "wrapper_of"):
            wrapper.wrapper_of = wrapped
        return wrapper

    return _inner
