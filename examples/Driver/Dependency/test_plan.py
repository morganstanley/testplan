#!/usr/bin/env python
"""
This example is to demonstrate driver scheduling following dependencies.
"""

import sys

from testplan import test_plan
from testplan.common.utils.context import context
from testplan.report.testing.styles import Style, StyleEnum
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from suites import MultiTCPSuite

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="TCPConnections",
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
)
def main(plan):
    """
    Testplan decorated main function to add and execute 2 MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    server_1 = TCPServer(name="server_1")
    client_1 = TCPClient(
        name="client_1",
        host=context("server_1", "{{host}}"),
        port=context("server_1", "{{port}}"),
    )
    server_2 = TCPServer(name="server_2")
    client_2 = TCPClient(
        name="client_2",
        host=context("server_2", "{{host}}"),
        port=context("server_2", "{{port}}"),
    )
    client_3 = TCPClient(
        name="client_3",
        host=context("server_2", "{{host}}"),
        port=context("server_2", "{{port}}"),
    )

    # If driver A is a dependency for driver B to start, we put driver A in the key
    # of dependencies dictionary and driver B as its corresponding value, so
    # visually driver A appears before driver B.

    # Here server_1 and server_2 will be started simutaneously to reduce the
    # overall test running time while not violating the dependencies.

    plan.add(
        MultiTest(
            name="MultiTCPDrivers",
            suites=[MultiTCPSuite()],
            environment=[
                server_1,
                server_2,
                client_1,
                client_2,
                client_3,
            ],
            dependencies={
                server_1: client_1,
                server_2: (client_2, client_3),
            },
        )
    )


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
