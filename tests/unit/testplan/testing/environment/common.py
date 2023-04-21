import time
from unittest.mock import call

from testplan.common.utils.timing import DEFAULT_INTERVAL
from testplan.testing.multitest.driver import Driver


def assert_lhs_before_rhs(mock_calls, lhs, rhs):
    assert mock_calls.index(call.post(lhs.name)) < mock_calls.index(
        call.pre(rhs.name)
    )


class MockDriver(Driver):
    def __init__(
        self,
        name,
        mock=None,
        check_wait=0,
        check_interval=DEFAULT_INTERVAL,
        total_wait=0,
        *args,
        **options
    ):
        super().__init__(name, **options)
        self._mock = mock
        self._check_wait = check_wait
        self._check_interval = check_interval
        self._total_wait = total_wait
        self._start_time = time.time()

    def pre_start(self):
        self._mock.pre(self.name)
        super().pre_start()

    def starting(self):
        self._start_time = time.time()
        super().starting()

    def post_start(self):
        self._mock.post(self.name)
        super().post_start()

    @property
    def started_check_interval(self):
        return self._check_interval

    def started_check(self):
        time.sleep(self._check_wait)
        if time.time() >= self._start_time + self._total_wait:
            return True
        return False
