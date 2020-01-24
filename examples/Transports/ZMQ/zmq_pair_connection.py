"""
Example of ZMQ Pair servers and clients.
"""

import zmq

from testplan.common.utils.context import context

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.zmq import ZMQServer, ZMQClient


@testsuite
class ZMQTestsuite(object):
    def setup(self, env):
        self.timeout = 5

    @testcase
    def send_and_receive_msg(self, env, result):
        # This test demonstrates sending and receiving messages in
        # both directions between a ZMQ client and server.
        #
        # The client sends a message to the server. Messages must have a b
        # before them to ensure they are sent as bytes in both python 2 and 3.
        msg = b"Hello server"
        result.log("Client is sending: {}".format(msg))
        env.client.send(data=msg, timeout=self.timeout)

        # The server receives this message.
        received = env.server.receive(timeout=self.timeout)
        result.equal(received, msg, "Server received")

        # The server sends a response to the client.
        resp = b"Hello client"
        result.log("Server is responding: {}".format(resp))
        env.server.send(data=resp, timeout=self.timeout)

        # The client receives this response.
        received = env.client.receive(timeout=self.timeout)
        result.equal(received, resp, "Client received")


def get_multitest(name):
    test = MultiTest(
        name=name,
        suites=[ZMQTestsuite()],
        environment=[
            # The server message pattern is defined as ZMQ PAIR.
            ZMQServer(
                name="server",
                host="127.0.0.1",
                port=0,
                message_pattern=zmq.PAIR,
            ),
            # The client message pattern is defined as ZMQ PAIR.
            ZMQClient(
                name="client",
                hosts=[context("server", "{{host}}")],
                ports=[context("server", "{{port}}")],
                message_pattern=zmq.PAIR,
            ),
        ],
    )
    return test
