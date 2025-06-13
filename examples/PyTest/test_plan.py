#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""Example to demonstrate PyTest integration with Testplan."""

import os
import sys

from testplan import test_plan
from testplan.common.utils.context import context
from testplan.testing import py_test
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


def before_start(env, result):
    result.log("Executing before start hook.")


def after_start(env, result):
    result.log("Executing after start hook.")
    env.server.accept_connection()


def before_stop(env, result):
    result.log("Executing before stop hook.")


def after_stop(env, result):
    result.log("Executing after stop hook.")


# Specify the name and description of the testplan via the decorator.
@test_plan(name="PyTest Example", description="PyTest basic example")
def main(plan):
    # Since this function is decorated with `@test_plan`, the first
    # argument will be a `Testplan` instance, to which we attach out test
    # targets. Here we will add a PyTest instance which targets the tests
    # in pytest_basics.py.
    plan.add(
        py_test.PyTest(
            name="My PyTest",
            description="PyTest example - pytest basics",
            target=[
                os.path.join(os.path.dirname(__file__), "pytest_tests.py")
            ],
            environment=[
                TCPServer(name="server", host="localhost", port=0),
                TCPClient(
                    name="client",
                    host=context("server", "{{host}}"),
                    port=context("server", "{{port}}"),
                ),
            ],
            before_start=before_start,
            after_start=after_start,
            before_stop=before_stop,
            after_stop=after_stop,
        )
    )


# Finally we trigger our main function when the script is run, and
# set the return status.
if __name__ == "__main__":
    res = main()
    sys.exit(res.exit_code)
