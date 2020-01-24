from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


@testsuite
class TCPSuite(object):
    @testcase
    def send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        bytes_sent = env.client.send_text("Hello")
        received = env.server.receive_text(size=bytes_sent)
        result.equal(received, "Hello", "Server received")

        bytes_sent = env.server.send_text("World")
        received = env.client.receive_text(size=bytes_sent)
        result.equal(received, "World", "Client received")


def make_multitest(idx=""):
    def accept_connection(env):
        print("Server accepts connection.")
        idx = env.server.accept_connection()
        if idx >= 0:
            print("Connection accepted from client.")

    return MultiTest(
        name="Test{}".format(idx),
        suites=[TCPSuite()],
        environment=[
            TCPServer(name="server"),
            TCPClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
            ),
        ],
        after_start=accept_connection,
    )
