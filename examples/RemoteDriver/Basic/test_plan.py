#!/usr/bin/env python

import os
import sys

# Check if the remote host has been specified in the environment. Remote
# hosts can only be Linux systems.
REMOTE_HOST = os.environ.get("TESTPLAN_REMOTE_HOST")
if not REMOTE_HOST:
    raise RuntimeError(
        "You must specify a remote Linux host via the TESTPLAN_REMOTE_HOST "
        "environment var to run this example."
    )

from testplan import test_plan
from testplan.common.remote.remote_driver import RemoteDriver
from testplan.common.remote.remote_service import RemoteService
from testplan.common.utils.context import context
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient
from testplan.testing.multitest import testsuite, testcase, MultiTest


# +-----+        +------+
# |Local| <----> |Remote|
# +-----+        +------+
#
# Testplan & Multitest on Local host
# TCPServer on Remote


@testsuite
class TCPTestsuite:
    """TCP tests for a server and a client."""

    def setup(self, env):
        """Will be executed before the testcase."""
        # Server accepts client connection.
        env.server.accept_connection()

    @testcase
    def send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        msg = env.client.cfg.name
        result.log("Client is sending: {}".format(msg))
        bytes_sent = env.client.send_text(msg)
        received = env.server.receive_text(size=bytes_sent)
        result.equal(received, msg, "Server received")

        response = "Hello {}".format(received)
        result.log("Server is responding: {}".format(response))
        bytes_sent = env.server.send_text(response)
        received = env.client.receive_text(size=bytes_sent)
        result.equal(received, response, "Client received")


@test_plan(name="RemoteDriverBasic", json_path="report.json")
def main(plan):

    # remote_service represents the RPyC server that runs on remote host
    remote_service = RemoteService(
        "rmt_svc",
        REMOTE_HOST,
        clean_remote=True,
    )

    # add the remote_service to plan so that it gets started,
    # and cleaned up after plan finished running as well
    plan.add_remote_service(remote_service)

    # args to be passed to TCPServer driver
    tcp_server_args = dict(
        name="server",
        host=REMOTE_HOST,
    )

    # define remote driver instance
    remote_tcp_server = RemoteDriver(
        remote_service=remote_service,  # via which remote_service shall the driver run
        driver_cls=TCPServer,  # what type of driver
        **tcp_server_args,  # args to driver class
    )

    plan.add(
        MultiTest(
            name="Remote TCP Server Test",
            suites=TCPTestsuite(),
            description="Running a TCP Server on remote host",
            environment=[
                remote_tcp_server,
                TCPClient(
                    name="client",
                    host=context("server", "{{host}}"),
                    port=context("server", "{{port}}"),
                ),
            ],
        )
    )


# Finally we trigger our main function when the script is run, and
# set the return status. Note that it has to be inverted because it's
# a boolean value.
if __name__ == "__main__":
    sys.exit(not main())
