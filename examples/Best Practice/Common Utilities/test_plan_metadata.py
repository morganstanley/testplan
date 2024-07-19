#!/usr/bin/env python
"""
Example demonstrating the usage of on-demand Driver metadata
extraction.
"""
import sys

from testplan import test_plan
from testplan.common.utils import helper
from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


def before_start(env, result):
    """
    Extracts driver metadata before environment startup.
    """
    helper.extract_driver_metadata(env, result)


def after_start(env, result):
    """
    Accepts TCPClient connection on TCPServer side and extracts driver
    metadata after startup.
    """
    env.server.accept_connection()
    helper.extract_driver_metadata(env, result)


@testsuite
class TCPSuite:
    @testcase
    def test_send_msg(self, env, result):
        """
        Simple testcase sending a message from client to server side at which it
        is received and the integrity is tested.
        """
        msg = "Hello Server!"
        msg_sent = env.client.send_text(msg)
        msg_received = env.server.receive_text(size=msg_sent)
        result.equal(msg_received, msg, "Message received on server side")


@test_plan(name="Example of Driver metadata extraction")
def main(plan):
    plan.add(
        MultiTest(
            name="Metadata extraction",
            suites=[TCPSuite()],
            environment=[
                TCPServer(
                    name="server",
                ),
                TCPClient(
                    name="client",
                    host=context("server", "{{host}}"),
                    port=context("server", "{{port}}"),
                ),
            ],
            before_start=before_start,
            after_start=after_start,
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
