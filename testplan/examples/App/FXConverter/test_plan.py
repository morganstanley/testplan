#!/usr/bin/env python
"""
This example is to test the converter.py binary application with the following
functionality:

    1. Connects to an external service that provides FX exchange rates.
    2. Accepts requests from clients i.e: 1000 GBP to be converted to EUR
    3. Requests the currency rate from the FX rates service. i.e: 1.15
    4. Responds to the client with the converted amount: i.e: 1150

    (Requests)        GBP:EUR:1000                 GBP:EUR
    ------------------          -----------------          ------------------
    |                | -------> |  converter.py | -------> | Exchange rates |
    |     Client     |          |       -       |          |    Server      |
    |                | <------- |  Application  | <------- |     Mock       |
    ------------------          -----------------          ------------------
    (Responses)          1150                       1.15
"""

import os
import re
import sys

from driver import FXConverter
from suites import EdgeCases, ConversionTests, RestartEvent
from testplan.testing.multitest import MultiTest

from testplan import test_plan
from testplan.common.utils.context import context
from testplan.report.testing.styles import Style, StyleEnum
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


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
    env.client.send(bytes('Stop'.encode('utf-8')))


def converter_environment():
    """
    MultiTest environment that will be made available within the testcases.
    """
    # Server that will respond with FX exchange rates.
    server = TCPServer(name='server')

    # Converter application that accepts configuration template that
    # after install process it will contain the host/port information of
    # the 'server' to connect to.
    # It also reads from the output file the address that the converter
    # listens for incoming connections and makes host/port info available
    # through its context so that the client can connect as well.
    converter_name = 'converter'
    config = 'converter.cfg'
    regexps = [re.compile(r'Converter started.'),
               re.compile(r'.*Listener on: (?P<listen_address>.*)')]
    converter = FXConverter(name=converter_name,
                            pre_args=[sys.executable],
                            binary=os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                'converter.py'),
                            args=[config],
                            install_files=[config],
                            log_regexps=regexps)

    # Client that connects to the converted application using host/port
    # information that FXConverter driver made available through its context.
    client = TCPClient(name='client',
                       host=context(converter_name, '{{host}}'),
                       port=context(converter_name, '{{port}}'))

    return [server, converter, client]


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(name='FXConverter',
           pdf_path='report.pdf',
           stdout_style=OUTPUT_STYLE,
           pdf_style=OUTPUT_STYLE)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    test = MultiTest(name='TestFXConverter',
                     suites=[ConversionTests(), EdgeCases(), RestartEvent()],
                     environment=converter_environment(),
                     after_start=after_start,
                     before_stop=before_stop)
    plan.add(test)


if __name__ == '__main__':
    res = main()
    print('Exiting code: {}'.format(res.exit_code))
    sys.exit(res.exit_code)
