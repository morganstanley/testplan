import pytest

from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.base import Driver

from testplan.common.utils.testing import check_report

from ..fixtures import base


class FailingDriver(Driver):
    def started_check(self):
        raise Exception


def test_driver_info_flag(mockplan):
    expected_report = (
        base.passing.report.expected_report_with_driver_and_driver_info_flag
    )
    multitest = MultiTest(
        name="MyTest",
        environment=[Driver("driver")],
        suites=[],
    )
    multitest.cfg.set_local("driver_info", True)
    mockplan.add(multitest)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)


def test_failing_driver_with_driver_info_flag(mockplan):
    expected_report = (
        base.failing.report.expected_report_with_failing_driver_and_driver_info_flag
    )
    multitest = MultiTest(
        name="MyTest",
        environment=[FailingDriver("driver")],
        suites=[],
    )
    multitest.cfg.set_local("driver_info", True)
    mockplan.add(multitest)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)
