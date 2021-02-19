from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

# Need to import from project root so that dependency
# is discoverable from interactive code reloader.
from my_tests.dependency import VALUE


@testsuite
class TCPSuite(object):
    @testcase
    def send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        bytes_sent = env.client.send_text("What is the value?")
        received = env.server.receive_text(size=bytes_sent)
        result.equal(received, "What is the value?", "Server received")

        bytes_sent = env.server.send_text(str(VALUE))
        received = env.client.receive_text(size=bytes_sent)
        result.equal(received, str(VALUE), "Client received")
