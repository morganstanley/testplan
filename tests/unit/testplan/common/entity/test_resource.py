"""Unit tests for the resource base."""
import time

import pytest

from testplan.common.entity import Resource, ResourceTimings
from testplan.common.utils.timing import Interval


class TestResourceTiming:
    """
    Tests resource records the start and stop timing
    """

    class DummyResource(Resource):
        def starting(self):
            time.sleep(0.2)  # 200ms for startup

        def stopping(self):
            time.sleep(0.1)  # 100ms for teardown

    def test_resource_timings(self):
        """
        Test start and stop methods record the time.
        """
        resource = self.DummyResource()
        resource.start()
        resource.wait(resource.STATUS.STARTED)
        assert len(resource.timer[ResourceTimings.RESOURCE_SETUP]) == 1
        assert isinstance(
            resource.timer[ResourceTimings.RESOURCE_SETUP][0], Interval
        )
        # there is some UnicodeEncodeError when using pytest.approx
        assert (
            0.1
            < resource.timer[ResourceTimings.RESOURCE_SETUP][0].elapsed
            < 0.3
        )

        resource.stop()
        resource.wait(resource.STATUS.STOPPED)
        assert len(resource.timer[ResourceTimings.RESOURCE_TEARDOWN]) == 1
        assert isinstance(
            resource.timer[ResourceTimings.RESOURCE_TEARDOWN][0], Interval
        )
        assert (
            0
            < resource.timer[ResourceTimings.RESOURCE_TEARDOWN][0].elapsed
            < 0.2
        )
