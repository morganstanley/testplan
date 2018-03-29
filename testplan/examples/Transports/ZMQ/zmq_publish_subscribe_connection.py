"""
Example of ZMQ Publish servers and Subscribe clients.
"""

import time

import zmq

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.zmq import ZMQServer, ZMQClient

from testplan.common.utils.context import context
from testplan.testing.multitest.suite import post_testcase


def after_start(env):
    # The subscribe client blocks all messages by default, the subscribe method
    # allows messages with a prefix that matches the topic_filter. Therefore an
    # empty string allows all messages through.
    env.client1.subscribe(topic_filter=b'')
    env.client2.subscribe(topic_filter=b'')
    # The ZMQ Subscribe client takes a bit longer to actually connect, no
    # connection results in dropped messages There is no way to verify the
    # connection currently so we add a small delay after start.
    time.sleep(1)

def flush_clients(name, self, env, result):
    env.client1.flush()
    env.client2.flush()
    # As above the sleep is to verify the clients have reconnected.
    time.sleep(1)


# The clients must be flushed after each test to remove any extra messages.
# This would occur when running many_publish_one_subscribe before
# one_publish_many_subscribe on client 2.
@post_testcase(flush_clients)
@testsuite
class ZMQTestsuite(object):
    def setup(self, env):
        self.timeout = 5

    @testcase
    def many_publish_one_subscribe(self, env, result):
        # Many publish servers send a message each to one subscription client as
        # shown in the diagram below:
        #
        # Server1 ---msg1---+
        #                   |
        #                   +---msg1 & msg2---> Client1
        #                   |
        # Server2 ---msg2---+
        #
        # Server 1 sends a unique message to client 1.
        msg1 = b'Hello 1'
        result.log('Server 1 is sending: {}'.format(msg1))
        env.server1.send(data=msg1, timeout=self.timeout)

        # Server 2 sends a unique message to client 1.
        msg2 = b'Hello 2'
        result.log('Server 2 is sending: {}'.format(msg2))
        env.server2.send(data=msg2, timeout=self.timeout)

        # Client 1 receives it's first message.
        received1 = env.client1.receive(timeout=self.timeout)

        # Client 1 receives it's second message.
        received2 = env.client1.receive(timeout=self.timeout)

        # Check the sent messages are the same as the received messages. Note
        # the messages may arrive in a different order.
        sent_msgs = set([msg1, msg2])
        received_msgs = set([received1, received2])
        result.equal(received_msgs, sent_msgs, 'Client 1 received')

    @testcase
    def one_publish_many_subscribe(self, env, result):
        # One publish server sends messages to many subscription clients as
        # shown in the diagram below:
        #
        #                  +---msg---> Client1
        #                  |
        # Server1 ---msg---+
        #                  |
        #                  +---msg---> Client2
        #
        # Server 1 sends a unique message to the clients it is connected to
        # (clients 1 & 2).
        msg = b'Hello 3'
        result.log('Server 1 is sending: {}'.format(msg))
        env.server1.send(data=msg, timeout=self.timeout)

        # Client 1 receives message from server 1.
        received1 = env.client1.receive(timeout=self.timeout)
        result.equal(received1, msg, 'Client 1 received')

        # Client 2 receives message from server 1.
        received2 = env.client2.receive(timeout=self.timeout)
        result.equal(received2, msg, 'Client 2 received')


def get_multitest(name):
    # The environment contains two ZMQServers and two ZMQClients connected as
    # in the diagrams below. This allows us to send messages from one publish
    # server to many subscription clients and from many subscription clients to
    # one publish server as in the examples above.
    #
    #               +------> Client1
    #               |
    # Server1 ------+
    #               |
    #               +------> Client2
    #
    # Server2 -------------> Client1
    test = MultiTest(name=name,
                     suites=[ZMQTestsuite()],
                     environment=[
                         # Both server's message patterns are defined as ZMQ
                         # PUB.
                         ZMQServer(name='server1',
                                   host='127.0.0.1',
                                   port=0,
                                   message_pattern=zmq.PUB),
                         ZMQServer(name='server2',
                                   host='127.0.0.1',
                                   port=0,
                                   message_pattern=zmq.PUB),
                         # Both client's message patterns are defined as ZMQ
                         # SUB.
                         ZMQClient(name='client1',
                                   hosts=[context('server1', '{{host}}'),
                                          context('server2', '{{host}}')],
                                   ports=[context('server1', '{{port}}'),
                                          context('server2', '{{port}}')],
                                   message_pattern=zmq.SUB),
                         ZMQClient(name='client2',
                                   hosts=[context('server1', '{{host}}')],
                                   ports=[context('server1', '{{port}}')],
                                   message_pattern=zmq.SUB)],
                     after_start=after_start)
    return test
