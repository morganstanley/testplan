"""TODO."""

from typing import Any
from dataclasses import dataclass

from testplan.common.report import Status


@dataclass
class DuckReport:
    status: Status
    val: Any


@dataclass
class DuckResult:
    report: DuckReport


class RunnableMixin:
    def run(self):
        return DuckResult(DuckReport(Status.PASSED, self._run()))


class RunnableTaskAdaptor(RunnableMixin):
    """Minimal callable to runnable task adaptor."""

    __slots__ = ("_target", "_args", "_kwargs")

    def __init__(self, target, *args, **kwargs):
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def _run(self):
        """Provide mandatory .run() task method."""
        return self._target(*self._args, **self._kwargs)

    def uid(self):
        """Provide mandatory .uid() task method."""
        return strings.uuid4()


class Runnable(RunnableMixin):
    """TODO."""

    def __init__(self, number, multiplier=2):
        """TODO."""
        self._number = number
        self._multiplier = multiplier
        self._stopped = False

    def _run(self):
        """TODO."""
        return self._number * self._multiplier

    def uid(self):
        """TODO."""
        return "{} * {}".format(self._number, self._multiplier)


def callable_to_runnable(number):
    """TODO."""
    return Runnable(number)


class NonRunnable:
    """TODO."""

    def __init__(self, number):
        """TODO."""
        self._number = number


class RunnableThatRaises(Runnable):
    """TODO."""

    def _run(self):
        """TODO."""
        raise Exception("123")


class RunnableStopRaises(Runnable):
    """TODO."""

    def stop(self):
        """TODO."""
        raise Exception("123")


class NonSerializableResult(Runnable):
    """TODO."""

    def _run(self):
        """TODO."""
        return lambda x: x * 2


class RunnableThatHungs(Runnable):
    """TODO."""

    def _run(self):
        """TODO."""
        while True:
            pass


class Multiplier(Runnable):
    """TODO."""

    pass


class Wrapper:
    """TODO."""

    InnerMultiplier = Multiplier


def callable_to_non_runnable(number):
    """TODO."""
    return NonRunnable(number)


def callable_to_none():
    """TODO."""

    def _inner():
        return None

    return _inner


def multiply(number, multiplier=2):
    """TODO."""
    return number * multiplier


def callable_to_adapted_runnable(number):
    """TODO."""
    return RunnableTaskAdaptor(multiply, number)
