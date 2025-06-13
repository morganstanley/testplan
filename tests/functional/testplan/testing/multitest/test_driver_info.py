import pytest

pytest.importorskip("plotly", reason="expected report generated with plotly")

from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.base import Driver
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

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
    expected_report = base.failing.report.expected_report_with_failing_driver_and_driver_info_flag
    multitest = MultiTest(
        name="MyTest",
        environment=[FailingDriver("driver")],
        suites=[],
    )
    multitest.cfg.set_local("driver_info", True)
    mockplan.add(multitest)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)


def test_multitest_drivers_connection_in_testplan(mockplan):
    expected_report = base.passing.report.expected_report_with_driver_connections_and_driver_info_flag
    server = TCPServer("server")
    client = TCPClient(
        name="client",
        host=context(server.cfg.name, "{{host}}"),
        port=context(server.cfg.name, "{{port}}"),
    )
    mtest = MultiTest(
        name="MyTest",
        suites=[],
        environment=[server, client],
    )
    mtest.cfg.set_local("driver_info", True)
    mockplan.add(mtest)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)
