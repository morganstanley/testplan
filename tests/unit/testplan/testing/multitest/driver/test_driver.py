"""Unit tests for the driver base."""

from testplan.testing.multitest.driver import base


class TestPrePostCallables(object):
    """Test pre/post callables."""

    class MyDriver(base.Driver):
        def __init__(self, **options):
            super(TestPrePostCallables.MyDriver, self).__init__(**options)
            self.pre_start_called = False
            self.post_start_called = False
            self.pre_stop_called = False
            self.post_stop_called = False

        def pre_start(self):
            self.pre_start_called = True

        def post_start(self):
            self.post_start_called = True

        def pre_stop(self):
            self.pre_stop_called = True

        def post_stop(self):
            self.post_stop_called = True

    def test_explicit_start_stop(self, runpath):
        """
        Test pre/post start callables when starting/stopping the driver
        explicitly.
        """
        driver = self.MyDriver(name='MyDriver', runpath=runpath)

        assert not driver.pre_start_called
        assert not driver.post_start_called

        driver.start()

        assert driver.pre_start_called
        assert not driver.post_start_called

        driver.wait(driver.STATUS.STARTED)

        assert driver.post_start_called
        assert not driver.pre_stop_called
        assert not driver.post_stop_called

        driver.stop()

        assert driver.pre_stop_called
        assert not driver.post_stop_called

        driver.wait(driver.STATUS.STOPPED)

        assert driver.post_stop_called

    def test_mgr_start_stop(self, runpath):
        """Test pre/post start callables when starting/stopping the driver
        implicitly via a context manager.
        """
        driver = self.MyDriver(name='MyDriver', runpath=runpath)

        assert not driver.pre_start_called
        assert not driver.post_start_called

        with driver:
            assert driver.pre_start_called
            assert driver.post_start_called
            assert not driver.pre_stop_called
            assert not driver.post_stop_called

        assert driver.pre_stop_called
        assert driver.post_stop_called
