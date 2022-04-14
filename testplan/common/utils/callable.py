"""Utilities related to python callables (functions, methods, classes etc.)"""

import inspect
import functools
from collections import namedtuple

WRAPPER_ASSIGNMENTS = functools.WRAPPER_ASSIGNMENTS + (
    "__tags__",
    "__tags_index__",
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


def wraps(
    wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=functools.WRAPPER_UPDATES
):
    """
    Custom wraps function that copies some additional attr than default.
    """

    def _inner(wrapper):
        wrapper = functools.update_wrapper(
            wrapper=wrapper,
            wrapped=wrapped,
            assigned=assigned,
            updated=updated,
        )
        return wrapper

    return _inner


def pre(*prefunctions):
    """
    Attaches function(s) to another function for systematic execution before
    said function, with the same arguments

    :param prefunction: function to execute before
    :type prefunction: ``callable``

    :return: function decorator
    :rtype: ``callable``
    """

    def outer(function):
        """
        Function decorator adding the execution of a prefunction
        """

        @wraps(function)
        def inner(*args, **kwargs):
            """
            Inner decorator body, executing the prefunctions and the
            function itself
            """
            for prefunction in prefunctions:
                prefunction(*args, **kwargs)
            return function(*args, **kwargs)

        return inner

    return outer


def post(*postfunctions):
    """
    Attaches function(s) to another function for systematic execution after
    said function, with the same arguments

    :param postfunction: function to execute after
    :type postfunction: ``callable``

    :return: function decorator
    :rtype: ``callable``
    """

    def outer(function):
        """
        Function decorator adding the excution of a postfunction
        """

        @wraps(function)
        def inner(*args, **kwargs):
            """
            Inner decorator body, executing the postfunctions and the
            function itself
            """
            result = function(*args, **kwargs)
            for postfunction in postfunctions:
                postfunction(*args, **kwargs)
            return result

        return inner

    return outer
