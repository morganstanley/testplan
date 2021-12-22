"""Utilities related to python callables (functions, methods, classes etc.)"""

import inspect
import functools
from collections import namedtuple
from collections.abc import Sequence

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


def functiondispatch(func, in_list=False):
    """
    Like `singledispatch` but dispatches by type of either the first
    argument, or the first element of that argument which is a sequence.
    """
    registry = {}

    def dispatch(*args):
        if not args:
            raise TypeError(
                f"{getattr(func, '__name__', 'dispatch function')}"
                " requires at least 1 positional argument"
            )
        if in_list and issubclass(args[0].__class__, Sequence) and args[0][0]:
            cls = args[0][0].__class__
        else:
            cls = args[0].__class__
        return registry[cls] if cls in registry else func

    def register(cls):
        def wrap(func):
            if cls in registry:
                raise ValueError(
                    "There is already a handler registered"
                    f" for {cls!r} in `@type_dispatch`"
                )
            registry[cls] = func
            return func

        return wrap

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return dispatch(*args)(*args, **kwargs)

    wrapper.register = register
    wrapper.dispatch = dispatch
    functools.update_wrapper(wrapper, func)
    return wrapper


def dispatchmethod(in_list=False):
    """
    Like `singledispatchmethod` but dispatches by type of either the first
    argument, or the first element of that argument which is a sequence.

    Supports wrapping existing descriptors and handles non-descriptor callables
    as instance methods.
    """

    class DispatchMethod(object):
        """`functiondispatch` generic method descriptor."""

        def __init__(self, func):
            if not callable(func) and not hasattr(func, "__get__"):
                raise TypeError(f"{func!r} is not callable or a descriptor")

            self.dispatcher = functiondispatch(func, in_list=in_list is True)
            self.func = func

        def register(self, cls):
            """
            Register a new implementation for the given `cls` on
            a generic method.
            """
            return self.dispatcher.register(cls)

        def __get__(self, obj, cls=None):
            def _method(*args, **kwargs):
                method = self.dispatcher.dispatch(*args)
                return method.__get__(obj, cls)(*args, **kwargs)

            _method.__isabstractmethod__ = self.__isabstractmethod__
            _method.register = self.register
            functools.update_wrapper(_method, self.func)
            return _method

        @property
        def __isabstractmethod__(self):
            return getattr(self.func, "__isabstractmethod__", False)

    if callable(in_list):
        # decorator is used without any argument
        return DispatchMethod(in_list)
    else:
        # argument `in_seq` is explicitly specified
        return DispatchMethod
