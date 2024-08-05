import pytest

from testplan.common.utils.testing import check_report
from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


from ..fixtures import base


def test_multitest_drivers_connection_in_testplan(mockplan):
    expected_report = (
        base.passing.report.expected_report_with_driver_connections_and_driver_info_flag
    )
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
