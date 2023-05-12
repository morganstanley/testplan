import time
from functools import reduce
from unittest.mock import call

from testplan.common.utils.timing import DEFAULT_INTERVAL
from testplan.testing.multitest.driver import Driver


def assert_lhs_before_rhs(mock_calls, lhs, rhs):
    assert mock_calls.index(call.post(lhs.name)) < mock_calls.index(
        call.pre(rhs.name)
    )


def assert_lhs_call_before_rhs_call(mock_calls, l_call, r_call):
    assert mock_calls.index(l_call) < mock_calls.index(r_call)


def assert_call_count(mock_calls, call, count):
    assert (
        reduce(lambda x, y: x + (1 if y == call else 0), mock_calls, 0)
        == count
    )


class MockDriver(Driver):
    def __init__(
        self,
        name,
        mock=None,
        check_wait=0,
        check_interval=DEFAULT_INTERVAL,
        total_wait=0,
        **options
    ):
        super().__init__(name, **options)
        self._mock = mock
        self._check_wait = check_wait
        self._check_interval = check_interval
        self._total_wait = total_wait
        self._start_time = None

    def pre_start(self):
        self._mock.pre(self.name)
        super().pre_start()

    def starting(self):
        self._start_time = time.time()
        super().starting()

    @property
    def started_check_interval(self):
        return self._check_interval

    def started_check(self):
        time.sleep(self._check_wait)
        if time.time() >= self._start_time + self._total_wait:
            return True
        return False

    def post_start(self):
        self._mock.post(self.name)
        super().post_start()


class FlakyDriver(Driver):
    def __init__(
        self,
        name,
        mock,
        pass_starting=True,
        pass_started_check=True,
        pass_stopping=True,
        pass_stopped_check=True,
        **options
    ):
        super().__init__(name, **options)
        self._mock = mock
        self._pass_starting = pass_starting
        self._pass_started_check = pass_started_check
        self._pass_stopping = pass_stopping
        self._pass_stopped_check = pass_stopped_check

    def pre_start(self):
        self._mock.pre_start(self.name)
        super().pre_start()

    def starting(self):
        if not self._pass_starting:
            raise RuntimeError("some random error")
        super().starting()

    def started_check(self):
        if not self._pass_started_check:
            raise RuntimeError("some random error")
        return True

    def post_start(self):
        self._mock.post_start(self.name)
        super().post_start()

    def pre_stop(self):
        self._mock.pre_stop(self.name)
        super().pre_stop()

    def stopping(self):
        if not self._pass_stopping:
            raise RuntimeError("some random error")
        super().stopping()

    def stopped_check(self):
        if not self._pass_stopped_check:
            raise RuntimeError("some random error")
        return True

    def post_stop(self):
        self._mock.post_stop(self.name)
        super().post_stop()
