"""Unit tests for the driver base."""
from dataclasses import dataclass

import pytest
from schema import SchemaError

from testplan.testing.multitest.driver import base


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

        driver.wait(driver.STATUS.STARTED)

        assert not driver.pre_stop_called
        assert not driver.post_stop_called

        driver.stop()

        assert driver.pre_stop_called
        assert driver.post_stop_called

        driver.wait(driver.STATUS.STOPPED)

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

    def test_start_stop_fn(self, runpath):
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

    def test_driver_stop_after_shutdown(self, runpath):
        """Test manually stopping a Driver after it has stopped."""

        driver = self.MyDriver(
            name="MyDriver",
            runpath=runpath,
            pre_start=pre_start_fn,
            post_start=post_start_fn,
            pre_stop=pre_stop_fn,
            post_stop=post_stop_fn,
        )

        driver.start()
        driver.wait(driver.STATUS.STARTED)
        assert driver.status == driver.status.STARTED

        driver.stop()
        driver.wait(driver.STATUS.STOPPED)
        assert driver.status == driver.status.STOPPED


class TestDriverMetadata:
    """
    Tests related to metadata objects and extraction from a custom driver.
    """

    class MyDriver(base.Driver):
        def __init__(self, **options):
            super(TestDriverMetadata.MyDriver, self).__init__(**options)
            self._test_attribute = None

        @property
        def test_attribute(self):
            return self._test_attribute

        def starting(self) -> None:
            self._test_attribute = "foo"
            super(TestDriverMetadata.MyDriver, self).starting()

        def stopping(self) -> None:
            self._test_attribute = "bar"
            super(TestDriverMetadata.MyDriver, self).stopping()

    @staticmethod
    def metadata_extractor_mydriver(driver: MyDriver):
        return base.DriverMetadata(
            name=driver.name,
            driver_metadata={"test_attribute": driver.test_attribute},
        )

    @staticmethod
    def metadata_extractor_invalid(mydriver):
        pass

    def test_to_dict(self):
        """
        Tests dictionary conversion of metadata objects.
        """
        metadata = base.DriverMetadata(
            name="testdriver",
            driver_metadata={
                "foo": "bar",
                "baz": "woo",
            },
        )
        test = metadata.to_dict()
        expected = {
            "foo": "bar",
            "baz": "woo",
        }
        assert test == expected

    def test_invalid_extractor_signature(self):
        """
        Tests whether the invalid signature of the metadata extractor raises.
        """
        with pytest.raises(SchemaError):
            TestDriverMetadata.MyDriver(
                name="mydriver",
                metadata_extractor=TestDriverMetadata.metadata_extractor_invalid,
            )

    def test_extract_mydriver_metadata(self):
        """
        Tests before and after start as well as after stop metadata.
        """
        my_driver = TestDriverMetadata.MyDriver(
            name="mydriver",
            metadata_extractor=TestDriverMetadata.metadata_extractor_mydriver,
        )
        test = my_driver.extract_driver_metadata().to_dict()
        expected = {"test_attribute": my_driver.test_attribute}
        assert test == expected

        my_driver.start()
        test = my_driver.extract_driver_metadata().to_dict()
        expected["test_attribute"] = "foo"
        assert test == expected

        my_driver.stop()
        test = my_driver.extract_driver_metadata().to_dict()
        expected["test_attribute"] = "bar"
        assert test == expected
