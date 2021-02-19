"""Tests FIX communication between a server and a client."""

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
    def send_and_receive_msg(self, env, result):
        """
        Basic FIX messaging between a FixServer and a FixClient.
        """
        # First we create a FIX message containing a single tag: 35=D
        msg = fixmsg({35: "D"})

        # We use the client to send that message over to the server.
        # The message is enriched with the expected session tags (49, 56 etc).
        env.client.send(msg)

        # We create a FIX message to describe what we expect the server to
        # receive. We expect the default FIX version FIX.4.2, the same value
        # for tag 35 as given, D, and the correct senderCompID and targetCompID.
        exp_msg = fixmsg(
            {
                8: "FIX.4.2",
                35: "D",
                49: env.client.sender,
                56: env.client.target,
            }
        )

        # We receive the message from the server.
        received = env.server.receive()

        # We assert that we expect a message that matches the message we sent.
        # We restrict the comparison to tags 8, 35, 49 and 56, since we want to
        # ignore the other message-level tags such as 9 and 10 that are
        # automatically added by the connectors.
        result.fix.match(
            exp_msg,
            received,
            description="Message sent by client match.",
            include_tags=[8, 35, 49, 56],
        )

        # Now, we create a response message from the server, confirming receipt
        # of order (message type 8)
        msg = fixmsg({35: "8"})

        # We use the server to send the response to the client.
        env.server.send(msg)

        # we can also create a heartbeat message (message type 0)
        heartbeat = fixmsg({35: "0"})
        # We use the server to send the heartbeat to the client.
        env.server.send(heartbeat)

        # We create a FIX message to describe what we expect the client to
        # receive. The default FIX version FIX.4.2 is expected, together with
        # the right senderCompID and targetCompID.
        exp_msg = fixmsg(
            {
                8: "FIX.4.2",
                35: "8",
                49: env.client.target,
                56: env.client.sender,
            }
        )

        exp_heartbeat = fixmsg(
            {
                8: "FIX.4.2",
                35: "0",
                49: env.client.target,
                56: env.client.sender,
            }
        )

        # We receive the message from the client.
        received = env.client.receive()
        received_heartbeat = env.client.receive()

        # We expect a message that matches the message we sent. We restrict the
        # comparison to tags 8, 35, 49 and 56, since we want to ignore the
        # other message-level tags such as 9 and 10 that are automatically
        # added by the connectors.
        result.fix.match(
            exp_msg,
            received,
            description="Message sent by server match.",
            include_tags=[8, 35, 49, 56],
        )
        result.fix.match(
            exp_heartbeat,
            received_heartbeat,
            description="Message sent by server match.",
            include_tags=[8, 35, 49, 56],
        )


def get_multitest():
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and a client connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    test = MultiTest(
        name="OverOneSession",
        suites=[FIXTestsuite()],
        environment=[
            FixServer(name="server", msgclass=FixMessage, codec=CODEC),
            FixClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                sender="TW",
                target="ISLD",
                msgclass=FixMessage,
                codec=CODEC,
            ),
        ],
    )
    return test
