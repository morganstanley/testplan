"""TODO."""

import inspect
import functools


WRAPPER_ASSIGNMENTS = functools.WRAPPER_ASSIGNMENTS + (
    '__tags__',
    '__tags_index__',
    'wrapper_of',
    'summarize',
    'summarize_num_passing',
    'summarize_num_failing'
)


def arity(function):
    """
    Return the arity of a function

    :param function: function
    :type function: ``function``

    :return: arity of the function
    :rtype: ``int``
    """
    return len(inspect.getargspec(function).args)


def getargspec(callable_):
    """
    Return an Argspec for any callable object

    :param callable_: a callable object
    :type callable_: ``callable``

    :return: argspec for the callable
    :rtype: ``inspect.ArgSpec``
    """
    if callable(callable_):
        if inspect.ismethod(callable_) or inspect.isfunction(callable_):
            return inspect.getargspec(callable_)
        else:
            return inspect.getargspec(callable_.__call__)
    else:
        raise ValueError("{} is not callable".format(callable_))


# backport from python 3.6, 2.7 version does not catch AttributeError
def update_wrapper(wrapper,
                   wrapped,
                   assigned=WRAPPER_ASSIGNMENTS,
                   updated=functools.WRAPPER_UPDATES):
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


def wraps(wrapped,
          assigned=WRAPPER_ASSIGNMENTS,
          updated=functools.WRAPPER_UPDATES):
    """
    Custom wraps function that uses the backported ``update_wrapper``.

    Also sets ``wrapper_of`` attribute for code highlighting, for methods that
    are decorated for the first time.
    """
    def _inner(wrapper):
        wrapper = update_wrapper(wrapper=wrapper, wrapped=wrapped,
                                 assigned=assigned, updated=updated)

        # When a method is decorated for the first time it will not have
        # `wrapper_of` attribute set, so `update_wrapper` won't be able to copy
        # it over. That's why we have to explicitly assign it here.
        if not hasattr(wrapped, 'wrapper_of'):
            wrapper.wrapper_of = wrapped
        return wrapper
    return _inner
