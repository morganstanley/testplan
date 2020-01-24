"""Tests FIX communication between a server and multiple clients."""

import os
import sys

try:
    sys.path.append(os.environ["PYFIXMSG_PATH"])
    import pyfixmsg
except (KeyError, ImportError):
    raise RuntimeError(
        "Download pyfixmsg library from "
        "https://github.com/Morgan-Stanley/pyfixmsg "
        "and set PYFIXMSG_PATH env var to the local path."
    )
try:
    SPEC_FILE = os.environ["FIX_SPEC_FILE"]
except KeyError:
    raise RuntimeError(
        "No spec file set. You should download "
        "https://github.com/quickfix/quickfix/blob/master/spec/FIX42.xml "
        "file and set FIX_SPEC_FILE to the local path."
    )

from pyfixmsg.fixmessage import FixMessage
from pyfixmsg.codecs.stringfix import Codec
from pyfixmsg.reference import FixSpec

from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.fix import FixServer, FixClient

CODEC = Codec(spec=FixSpec(SPEC_FILE))


def fixmsg(source):
    """
    Factory function that forces the codec to our given spec and avoid
    passing codec to serialisation and parsing methods.
    The codec defaults to a reasonable parser but without repeating groups.
    An alternative method is to use the ``to_wire`` and ``from_wire`` methods
    to serialise and parse messages and pass the codec explicitly.
    """
    # python 2 and 3 compatibility
    msg = FixMessage(source)
    msg.codec = CODEC
    return msg


@testsuite
class FIXTestsuite(object):
    @testcase
    def send_and_receive_msgs(self, env, result):
        """
        Basic FIX messaging with many FixClients connecting to one FixServer.
        """
        # First we create a FIX message with tag: 35=D and a comment in tag 58.
        msg1 = fixmsg({35: "D", 58: "first client"})
        # We use the first client to send that message over to the server.
        # The message is enriched with the expected session tags (49, 56 etc).
        env.client1.send(msg1)
        # We create a FIX message to describe what we expect the server to
        # receive. We expect the default FIX version FIX.4.2, the same value
        # for tag 35 as given, D, and the correct senderCompID and targetCompID
        # (those from the first client).
        exp_msg1 = fixmsg(
            {
                8: "FIX.4.2",
                35: "D",
                49: env.client1.sender,
                56: env.client1.target,
                58: "first client",
            }
        )
        # We receive the message from the server. Since the server now has
        # multiple connections, we also need to specify which connection
        # we want to receive the message from. This is indicated through the
        # (senderCompID, targetCompID) pair passed in.
        received1 = env.server.receive(
            (env.client1.target, env.client1.sender)
        )
        # We assert and restrict the comparison to tags 8, 35, 49, 56 and 58,
        # since we want to ignore the other message-level tags such as 9 and 10
        # that are automatically added by the connectors.
        result.fix.match(
            exp_msg1,
            received1,
            description="Message sent by client 1 match.",
            include_tags=[8, 35, 49, 56, 58],
        )

        # We create a very similar message, but with a different comment.
        msg2 = fixmsg({35: "D", 58: "second client"})
        # Now, we send the message from the second client.
        # The message is enriched with the expected session tags (49, 56 etc).
        env.client2.send(msg2)

        # The message we expect is almost identical, except for senderCompID
        # and targetCompID tags, which now identify the second connection.
        exp_msg2 = fixmsg(
            {
                8: "FIX.4.2",
                35: "D",
                49: env.client2.sender,
                56: env.client2.target,
                58: "second client",
            }
        )
        # We receive the message and this time we want to receive from the
        # second client. So, we specify to the server that it should receive
        # from the second connection.
        received2 = env.server.receive(
            (env.client2.target, env.client2.sender)
        )
        # We assert and restrict the comparison to tags 8, 35, 49, 56 and 58,
        # since we want to ignore the other message-level tags such as 9 and 10
        # that are automatically added by the connectors.
        result.fix.match(
            exp_msg2,
            received2,
            description="Message sent by client 2 match.",
            include_tags=[8, 35, 49, 56, 58],
        )

        # Now, we create a response message from the server,
        # confirming receipt of order (message type 8).
        msg = fixmsg({35: "8"})
        # We use the server to send the response to both clients in turn.
        env.server.send(msg, (env.client1.target, env.client1.sender))
        env.server.send(msg, (env.client2.target, env.client2.sender))
        # We create a FIX message to describe what we expect the clients to
        # receive. The default FIX version FIX.4.2 is expected in both messages.
        # However, the senderCompID and targetCompID differ for the two clients.
        exp_msg1 = fixmsg(
            {
                8: "FIX.4.2",
                35: "8",
                49: env.client1.target,
                56: env.client1.sender,
            }
        )
        exp_msg2 = fixmsg(
            {
                8: "FIX.4.2",
                35: "8",
                49: env.client2.target,
                56: env.client2.sender,
            }
        )
        # We receive the message from the clients.
        received1 = env.client1.receive()
        received2 = env.client2.receive()
        # We expect the messages matche the message we sent. We restrict the
        # comparison to tags 8, 35, 49 and 56, since we want to ignore the
        # other message-level tags such as 9 and 10 that are automatically
        # added by the connectors.
        result.fix.match(
            exp_msg1,
            received1,
            description="Msg sent by server to client 1 match.",
            include_tags=[8, 35, 49, 56],
        )
        result.fix.match(
            exp_msg2,
            received2,
            description="Msg sent by server to client 2 match.",
            include_tags=[8, 35, 49, 56],
        )


def get_multitest():
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and two clients connecting using the context
    functionality that retrieves host/port of the server after is started.

       ------------- client1
       |
    server
       |
       ------------- client2

    """
    test = MultiTest(
        name="OverTwoSessions",
        suites=[FIXTestsuite()],
        environment=[
            FixServer(name="server", msgclass=FixMessage, codec=CODEC),
            FixClient(
                name="client1",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                sender="TW",
                target="ISLD",
                msgclass=FixMessage,
                codec=CODEC,
            ),
            FixClient(
                name="client2",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                sender="TW2",
                target="ISLD",
                msgclass=FixMessage,
                codec=CODEC,
            ),
        ],
    )
    return test
