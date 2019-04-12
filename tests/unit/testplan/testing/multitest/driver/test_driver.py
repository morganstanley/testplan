"""TODO."""

from testplan.testing.multitest.driver.base import Driver


def test_pre_post_callables():
    class MyDriver(Driver):
        def __init__(self, **options):
            super(MyDriver, self).__init__(**options)
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

    driver = MyDriver(name='MyDriver')

    assert driver.pre_start_called is False
    assert driver.post_start_called is False
    driver.start()
    assert driver.pre_start_called is True
    assert driver.post_start_called is False
    driver.wait(driver.STATUS.STARTED)
    assert driver.post_start_called is True
    assert driver.pre_stop_called is False
    assert driver.post_stop_called is False
    driver.stop()
    assert driver.pre_stop_called is True
    assert driver.post_stop_called is False
    driver.wait(driver.STATUS.STOPPED)
    assert driver.post_stop_called is True

    driver = MyDriver(name='MyDriver')

    assert driver.pre_start_called is False
    assert driver.post_start_called is False
    with driver:
        assert driver.pre_start_called is True
        assert driver.post_start_called is True
        assert driver.pre_stop_called is False
        assert driver.post_stop_called is False
    assert driver.pre_stop_called is True
    assert driver.post_stop_called is True
