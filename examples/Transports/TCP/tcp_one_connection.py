"""Tests TCP communication between a server and a client."""

from testplan.common.utils.context import context

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


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


def get_multitest(name):
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and a client connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    test = MultiTest(
        name=name,
        suites=[TCPTestsuite()],
        environment=[
            TCPServer(name="server"),
            TCPClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
            ),
        ],
    )
    return test
