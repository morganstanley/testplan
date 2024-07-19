import os
import re
import sys

import pytest

from testplan.common.utils.testing import check_report
from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from .driver import FXConverter

from ...fixtures import base


def after_start(env):
    """
    Called right after MultiTest starts.
    """
    # Server accepts connection request by convert app.
    env.server.accept_connection()


def before_stop(env, result):
    """
    Called right before MultiTest stops.
    """
    # Clients sends stop command to the converted app.
    env.client.send(bytes("Stop".encode("utf-8")))


def converter_environment():
    """
    MultiTest environment that will be made available within the testcases.
    """
    # Server that will respond with FX exchange rates.
    server = TCPServer(name="server")

    # Converter application that accepts configuration template that
    # after install process it will contain the host/port information of
    # the 'server' to connect to.
    # It also reads from the output file the address that the converter
    # listens for incoming connections and makes host/port info available
    # through its context so that the client can connect as well.
    converter_name = "converter"
    config = "converter.cfg"
    regexps = [
        re.compile(r"Converter started."),
        re.compile(r".*Listener on: (?P<listen_address>.*)"),
    ]
    converter = FXConverter(
        name=converter_name,
        pre_args=[sys.executable],
        binary=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "converter.py"
        ),
        args=[config],
        install_files=[
            os.path.join(os.path.dirname(os.path.abspath(__file__)), config)
        ],
        log_regexps=regexps,
    )

    # Client that connects to the converted application using host/port
    # information that FXConverter driver made available through its context.
    client = TCPClient(
        name="client",
        host=context(converter_name, "{{host}}"),
        port=context(converter_name, "{{port}}"),
    )

    return [server, converter, client]


def test_multitest_drivers_in_testplan(mockplan):
    expected_report = (
        base.passing.report.expected_report_with_driver_and_driver_connection_flag
    )
    mtest = MultiTest(
        name="MyTest",
        suites=[],
        environment=converter_environment(),
        after_start=after_start,
        before_stop=before_stop,
    )
    mtest.cfg.set_local("driver_connection", True)
    mockplan.add(mtest)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)
