"""Utilities for exception handling."""

import logging
import functools
import inspect

LOGGER = logging.getLogger(__name__)


def should_raise(exception, item, args=None, kwargs=None, pattern=None):
    """
    "Utility that validates callable should raise specific exception.

    :param exception: Exception should be raised.
    :type exception: ``Exception``
    :param item: Callable that should raise.
    :type item: ``callable``
    :param args: Callable args.
    :type args: ``tuple``
    :param kwargs: Callable kwargs.
    :type kwargs: ``dict``
    :param pattern: Compiled regex pattern that needs to match the exception.
    :type pattern: Compiled ``regex``
    """
    try:
        item(*args or tuple(), **kwargs or {})
    except Exception as exc:
        assert isinstance(exc, exception)
        if pattern:
            if not pattern.match(str(exc)):
                raise Exception('Exception msg incorrect - {}'.format(exc))
    else:
        raise Exception('Should raise {} exception.'.format(exception))


def suppress_exception(logger=LOGGER):
    """
    Suppress & log exceptions for the given function.

    This is mostly used during exporters steps, as we would like to
    return the original retcode from testplan run, without raising any
    non-test-related errors.
    """
    def _wrapper(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.exception(exc)
        return _inner
    return _wrapper


def _safe_repr(obj):
    """
    Exception safe repr()
    """
    try:
        return repr(obj)
    except Exception:
        return '<?>'


def _format_args(args):
    """
    Format function arguments for a stack trace
    """
    def _format_line(line):
        """
        Format a single line
        """
        if len(line) > 120:
            return '        {}...'.format(line[:113])
        else:
            return '        {}'.format(line)
    rargs = [_safe_repr(arg) for arg in args]
    rargs_size = sum(len(rarg) for rarg in rargs)

    if rargs_size > 80:
        return '(\n{})'.format(',\n'.join(
            [_format_line(rarg) for rarg in rargs]))
    else:
        return '({})'.format(', '.join(rargs))


def format_trace(trace, exception=None):
    """
    Return a string containing a stack trace, including an attempt
    at displaying argument values, within a certain size.

    Example::

      >>> format_trace(inspect.trace(), exception)
    """
    output = ['Traceback (most recent call last):\n']
    for frame, fpath, line, parent, code, _ in trace:
        fmtted_args = ''
        try:
            args = inspect.getargvalues(frame)
            args = [args.locals[name] for name in args.args]
            fmtted_args = _format_args(args)
        except Exception:
            pass
        finally:
            del frame
        output.append(
            '  File "{}", line {}, in {}{}\n'.format(
                fpath, line, parent, fmtted_args))
        for line in code or []:
            output.append('    {}\n'.format(line.strip()))
    if exception is not None:
        output.append('{}: {}'.format(
            getattr(type(exception), '__name__', '<Unknown>'), exception))
    return ''.join(output)
