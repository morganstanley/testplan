#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""Example to demonstrate PyTest integration with Testplan."""
import sys

import testplan
from testplan.testing import py_test

from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient
from testplan.common.utils.context import context


# Specify the name and description of the testplan via the decorator.
@testplan.test_plan(name="PyTestExample", description="PyTest basic example")
def main(plan):
    # Now we are inside a function that will be passed a plan object, we
    # can add tests to this plan. Here we will add a PyTest instance that
    # targets the tests in pytest_basics.py.
    plan.add(
        py_test.PyTest(
            name="PyTest",
            description="PyTest example - pytest basics",
            target=["pytest_tests.py"],
            environment=[
                TCPServer(name="server", host="localhost", port=0),
                TCPClient(
                    name="client",
                    host=context("server", "{{host}}"),
                    port=context("server", "{{port}}"),
                ),
            ],
        )
    )


# Finally we trigger our main function when the script is run, and
# set the return status.
if __name__ == "__main__":
    res = main()
    sys.exit(res.exit_code)
