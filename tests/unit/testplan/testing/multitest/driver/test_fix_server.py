"""Unit tests for TCP Server driver."""

import os
import pytest

from tests.helpers.pytest_test_filters import skip_on_windows

pytestmark = skip_on_windows(
    reason='TCP cannot be used on platform "{}"'.format(os.name)
)

pytest.importorskip("pyfixmsg")

from pyfixmsg.fixmessage import FixMessage
from pyfixmsg.codecs.stringfix import Codec
from pyfixmsg.reference import FixSpec
from testplan.testing.multitest.driver.fix import FixServer, FixClient

SPEC_FILE = os.environ["FIX_SPEC_FILE"]
CODEC = Codec(spec=FixSpec(SPEC_FILE))


@pytest.fixture(scope="function")
def fix_server(mockplan):
    """Start and yield a TCP server driver."""
    server = FixServer(
        name="server",
        msgclass=FixMessage,
        codec=CODEC,
    )
    server.parent = mockplan

    with server:
        yield server


@pytest.fixture(scope="function")
def fix_client(fix_server, mockplan):
    """Start and yield a TCP client driver."""

    client = FixClient(
        name="client",
        host=fix_server.host,
        port=fix_server.port,
        sender="TW",
        target="ISLD",
        msgclass=FixMessage,
        codec=CODEC,
    )
    client.parent = mockplan

    with client:
        yield client


def fixmsg(source):
    msg = FixMessage(source)
    msg.codec = CODEC
    return msg


def test_successive_send(fix_client, fix_server):
    msg1 = fixmsg(
        {
            8: "FIX.4.2",
            35: "D",
        }
    )
    msg2 = fixmsg(
        {
            8: "FIX.4.2",
            35: "8",
        }
    )

    for sender, receiver in (
        (fix_client, fix_server),
        (fix_server, fix_client),
    ):

        sender.send(msg1)
        sender.send(msg2)

        rcv1 = receiver.receive()
        rcv2 = receiver.receive()

        assert rcv1[35] == "D"
        assert rcv2[35] == "8"
