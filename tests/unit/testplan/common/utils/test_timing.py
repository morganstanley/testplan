import time
import datetime

import pytest

from testplan.common.utils.timing import Interval, Timer, utcnow


def test_interval():
    begin = datetime.datetime(2017, 1, 1, 10, 20, 0)
    end = datetime.datetime(2017, 1, 1, 10, 20, 10)
    interval = Interval(begin, end)

    assert interval.elapsed == 10


class TestTimer:
    def test_start(self):
        """`Timer.start` should create an `Interval` that has `start` attribute set."""
        timer = Timer()

        assert "my_key" not in timer

        prev_now = utcnow()
        time.sleep(0.001)

        timer.start("my_key")

        assert prev_now < timer["my_key"][-1].start
        assert timer["my_key"][-1].end is None

    def test_start_twice(self):
        """`Timer.start` should add another entry it was already called before for the given key."""
        timer = Timer()

        with timer.record("my_key"):
            pass

        timer.start("my_key")
        assert len(timer["my_key"]) == 2

    def test_end(self):
        """`timer.end` should update the matching `Interval.end` for the given key."""
        timer = Timer()

        # Explicitly set value for testing
        # don't care about start
        timer["my_key"] = [Interval("foo", None)]

        prev_now = utcnow()

        time.sleep(0.001)

        timer.end("my_key")

        assert prev_now < timer["my_key"][-1].end

    def test_end_overwrite(self):
        """`timer.end` cannot overwrite previous `end` value for the given key."""
        timer = Timer()

        with timer.record("my_key"):
            pass

        time.sleep(0.001)
        with pytest.raises(KeyError):
            timer.end("my_key")

    def test_end_fail(self):
        """`record_end` must fail when no entry if found for a given key."""
        timer = Timer()

        with pytest.raises(KeyError):
            timer.end("my_key")

    def test_record(self):
        """`Timer.record` should record an interval for the given context."""
        sleep_duration = 1
        sleeper_delta = 0.25  # func call lasts a little bit longer

        def sleeper():
            time.sleep(sleep_duration)

        timer = Timer()
        with timer.record("my_key"):
            sleeper()

        # TODO check why 1 (sleep_durtion) <= 0.9999 (elapsed)
        # assert sleep_duration <= timer['my_key'][-1].elapsed <= sleep_duration + sleeper_delta
