#!/usr/bin/env python
"""
This example is to showcase the driver connection functionality.
"""

import os
import re
import sys

from drivers import (
    CustomTCPClient,
    WritingDriver,
    ReadingDriver,
    UnconnectedDriver,
)

from testplan import test_plan
from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.tcp import TCPServer


def environment():
    """
    MultiTest environment that will be made available within the testcases.
    """
    server = TCPServer(name="server")
    client = CustomTCPClient(
        name="client",
        host=context("server", "{{host}}"),
        port=context("server", "{{port}}"),
    )

    writer_name = "WritingDriver"
    writer_regexps = [
        re.compile(r".*Writing to file: (?P<file_path>.*)"),
    ]
    writer = WritingDriver(
        name=writer_name,
        pre_args=[sys.executable],
        binary=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "writer.py"
        ),
        log_regexps=writer_regexps,
    )
    reader_regexps = [
        re.compile(r".*Reading from file: (?P<file_path>.*)"),
    ]
    reader = ReadingDriver(
        name="ReadingDriver",
        pre_args=[sys.executable],
        binary=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "reader.py"
        ),
        args=[context(writer_name, "{{file_path}}")],
        log_regexps=reader_regexps,
    )

    unconnected = UnconnectedDriver("unconnected_driver")

    return [server, client, writer, reader, unconnected]


@test_plan(name="DriverConnectionExample", driver_connection=True)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    test = MultiTest(
        name="DriverConnectionExample",
        suites=[],
        environment=environment(),
    )
    plan.add(test)


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
