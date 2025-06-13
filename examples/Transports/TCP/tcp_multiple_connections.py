"""
Tests TCP communication between a server that accepts multiple clients.
"""

from testplan.common.utils.context import context

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


@testsuite
class TCPTestsuite:
    """TCP tests for a server and 2 clients."""

    def __init__(self):
        self._conn_idx = {}

    def setup(self, env):
        """Will be executed before the testcase."""
        # Client 1 connects, server accepts and stores the connection index,
        env.client1.connect()
        self._conn_idx["client1"] = env.server.accept_connection()

        # Client 2 connects, server accepts and stores the connection index,
        env.client2.connect()
        self._conn_idx["client2"] = env.server.accept_connection()

    @testcase
    def send_and_receive_msg(self, env, result):
        """
        The TCP communication is the following:
            1. Client 1 sends a message.
            2. Client 2 sends a message:
            3. Server receives client 1 message.
            4. Server responds to client 1.
            5. Server receives client 2 message.
            6. Server responds to client 2.
        """
        idx1 = self._conn_idx["client1"]
        idx2 = self._conn_idx["client2"]

        msg1 = env.client1.cfg.name
        result.log("Client1 is sending: {}".format(msg1))
        bytes_sent1 = env.client1.send_text(msg1)

        msg2 = env.client2.cfg.name
        result.log("Client2 is sending: {}".format(msg2))
        bytes_sent2 = env.client2.send_text(msg2)

        received = env.server.receive_text(size=bytes_sent1, conn_idx=idx1)
        result.equal(received, msg1, "Server received")

        response = "Hello {}".format(received)
        result.log("Server is responding: {}".format(response))
        resp_size = env.server.send_text(response, conn_idx=idx1)
        result.equal(
            env.client1.receive_text(size=resp_size),
            response,
            "Client1 received",
        )

        received = env.server.receive_text(size=bytes_sent2, conn_idx=idx2)
        result.equal(received, msg2, "Server received")

        response = "Hello {}".format(received)
        result.log("Server is responding: {}".format(response))
        resp_size = env.server.send_text(response, conn_idx=idx2)
        result.equal(
            env.client2.receive_text(size=resp_size),
            response,
            "Client2 received",
        )

    @testcase
    def reconnect_a_client(self, env, result):
        """
        Tests the ability to reconnect a client within the testcase.
        After reconnection, the server accepts the new connection
        and assignes a new connection index for this client.
        """
        prev_idx = self._conn_idx["client1"]
        env.client1.reconnect()
        self._conn_idx["client1"] = env.server.accept_connection()
        new_idx = self._conn_idx["client1"]

        result.gt(new_idx, prev_idx, "Client has new connection index")
        msg = "Connection old index: {}, new index: {}".format(
            prev_idx, new_idx
        )
        bytes_sent = env.client1.send_text(msg)
        # Default conn_idx tp receive is the most recent.
        received = env.server.receive_text(size=bytes_sent)
        result.log(received)


def get_multitest(name):
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and 2 clients connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    test = MultiTest(
        name=name,
        suites=[TCPTestsuite()],
        environment=[
            TCPServer(name="server"),
            TCPClient(
                name="client1",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                connect_at_start=False,
            ),
            TCPClient(
                name="client2",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                connect_at_start=False,
            ),
        ],
    )
    return test
