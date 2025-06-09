"""Unit tests for the driver base."""

from dataclasses import dataclass
import time

import pytest
from schema import SchemaError

from testplan.testing.multitest.driver import base
from testplan.common.utils.timing import Interval
from testplan.common.entity import ResourceTimings


def pre_start_fn(driver):
    assert driver.pre_start_called
    driver.pre_start_fn_called = True


def post_start_fn(driver):
    assert driver.post_start_called
    driver.post_start_fn_called = True


def pre_stop_fn(driver):
    assert driver.pre_stop_called
    driver.pre_stop_fn_called = True


def post_stop_fn(driver):
    assert driver.post_stop_called
    driver.post_stop_fn_called = True


class TestPrePostCallables:
    """Test pre/post callables."""

    class MyDriver(base.Driver):
        def __init__(self, **options):
            super(TestPrePostCallables.MyDriver, self).__init__(**options)
            self.pre_start_called = False
            self.post_start_called = False
            self.pre_stop_called = False
            self.post_stop_called = False

            self.pre_start_fn_called = False
            self.post_start_fn_called = False
            self.pre_stop_fn_called = False
            self.post_stop_fn_called = False

        def pre_start(self):
            self.pre_start_called = True
            super(TestPrePostCallables.MyDriver, self).pre_start()

        def post_start(self):
            self.post_start_called = True
            super(TestPrePostCallables.MyDriver, self).post_start()

        def pre_stop(self):
            self.pre_stop_called = True
            super(TestPrePostCallables.MyDriver, self).pre_stop()

        def post_stop(self):
            self.post_stop_called = True
            super(TestPrePostCallables.MyDriver, self).post_stop()

    def test_explicit_start_stop(self, runpath):
        """
        Test pre/post start methods when starting/stopping the driver
        explicitly.
        """
        driver = self.MyDriver(name="MyDriver", runpath=runpath)

        assert not driver.pre_start_called
        assert not driver.post_start_called

        driver.start()

        assert driver.pre_start_called
        assert driver.post_start_called

        assert not driver.pre_stop_called
        assert not driver.post_stop_called

        driver.stop()

        assert driver.pre_stop_called
        assert driver.post_stop_called

    def test_explicit_async_start_stop(self, runpath):
        """
        Test pre/post start methods when starting/stopping the driver
        explicitly, with this standalone driver set at async mode
        """
        driver = self.MyDriver(
            name="MyDriver", runpath=runpath, async_start=True
        )

        assert not driver.pre_start_called
        driver.start()
        assert driver.pre_start_called

        assert not driver.post_start_called
        driver.wait(driver.status.STARTED)
        assert driver.post_start_called

        assert not driver.pre_stop_called
        driver.stop()
        assert driver.pre_stop_called

        assert not driver.post_stop_called
        driver.wait(driver.status.STOPPED)
        assert driver.post_stop_called

    def test_mgr_start_stop(self, runpath):
        """Test pre/post start methods when starting/stopping the driver
        implicitly via a context manager.
        """
        driver = self.MyDriver(name="MyDriver", runpath=runpath)

        assert not driver.pre_start_called
        assert not driver.post_start_called

        with driver:
            assert driver.pre_start_called
            assert driver.post_start_called
            assert not driver.pre_stop_called
            assert not driver.post_stop_called

        assert driver.pre_stop_called
        assert driver.post_stop_called

    def test_mgr_start_stop_fn(self, runpath):
        """Test pre/post start callables when starting/stopping the driver
        implicitly via a context manager."""

        driver = self.MyDriver(
            name="MyDriver",
            runpath=runpath,
            pre_start=pre_start_fn,
            post_start=post_start_fn,
            pre_stop=pre_stop_fn,
            post_stop=post_stop_fn,
        )

        assert not driver.pre_start_fn_called
        assert not driver.post_start_fn_called

        with driver:
            assert driver.pre_start_fn_called
            assert driver.post_start_fn_called
            assert not driver.pre_stop_fn_called
            assert not driver.post_stop_fn_called

        assert driver.pre_stop_fn_called
        assert driver.post_stop_fn_called

    def test_driver_status(self, runpath):
        """Test driver status after certain operations."""

        driver = self.MyDriver(
            name="MyDriver",
            runpath=runpath,
            pre_start=pre_start_fn,
            post_start=post_start_fn,
            pre_stop=pre_stop_fn,
            post_stop=post_stop_fn,
        )

        driver.start()
        assert driver.status == driver.status.STARTED

        driver.stop()
        assert driver.status == driver.status.STOPPED


class TestDriverTiming:
    """
    Tests driver records the start and stop timing
    """

    class DummyDriver(base.Driver):
        def starting(self):
            time.sleep(0.2)  # 200ms for startup

        def stopping(self):
            time.sleep(0.1)  # 100ms for teardown

    def test_driver_timings(self):
        """
        Test start and stop methods record the time.
        """
        driver = self.DummyDriver(name="MyDriver")
        driver.start()
        assert len(driver.timer[ResourceTimings.RESOURCE_SETUP]) == 1
        assert isinstance(
            driver.timer[ResourceTimings.RESOURCE_SETUP][0], Interval
        )
        # there is some UnicodeEncodeError when using pytest.approx
        assert (
            0.1 < driver.timer[ResourceTimings.RESOURCE_SETUP][0].elapsed < 0.3
        )

        driver.stop()
        assert len(driver.timer[ResourceTimings.RESOURCE_TEARDOWN]) == 1
        assert isinstance(
            driver.timer[ResourceTimings.RESOURCE_TEARDOWN][0], Interval
        )
        assert (
            0
            < driver.timer[ResourceTimings.RESOURCE_TEARDOWN][0].elapsed
            < 0.2
        )
