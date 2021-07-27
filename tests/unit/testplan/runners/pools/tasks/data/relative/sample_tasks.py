"""TODO."""

from testplan.runners import RunnableTaskAdaptor


class Runnable(object):
    """TODO."""

    def __init__(self, number, multiplier=2):
        """TODO."""
        self._number = number
        self._multiplier = multiplier
        self._stopped = False

    def run(self):
        """TODO."""
        return self._number * self._multiplier

    def uid(self):
        """TODO."""
        return "{} * {}".format(self._number, self._multiplier)


def callable_to_runnable(number):
    """TODO."""
    return Runnable(number)


class NonRunnable(object):
    """TODO."""

    def __init__(self, number):
        """TODO."""
        self._number = number


class RunnableThatRaises(Runnable):
    """TODO."""

    def run(self):
        """TODO."""
        raise Exception("123")


class RunnableStopRaises(Runnable):
    """TODO."""

    def stop(self):
        """TODO."""
        raise Exception("123")


class NonSerializableResult(Runnable):
    """TODO."""

    def run(self):
        """TODO."""
        return lambda x: x * 2


class RunnableThatHungs(Runnable):
    """TODO."""

    def run(self):
        """TODO."""
        while True:
            pass


class Multiplier(Runnable):
    """TODO."""

    pass


class Wrapper(object):
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
