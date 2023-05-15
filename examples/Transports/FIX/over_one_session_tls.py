"""Tests FIX communication between a server and a client."""

import os
from pathlib import Path
import sys


try:
    sys.path.append(os.environ["PYFIXMSG_PATH"])
    import pyfixmsg
except (KeyError, ImportError):
    raise RuntimeError(
        "Download pyfixmsg library from "
        "https://github.com/morganstanley/pyfixmsg "
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
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.fix import FixServer, FixClient
from testplan.common.utils.sockets.tls import SimpleTLSConfig

from over_one_session import FIXTestsuite

CODEC = Codec(spec=FixSpec(SPEC_FILE))


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


def get_tls_multitest():
    """
    Creates and returns a new MultiTest instance to be added to the plan.
    The environment is a server and a client connecting using the context
    functionality that retrieves host/port of the server after is started.
    """
    test = MultiTest(
        name="OverOneSession With TLS",
        suites=[FIXTestsuite()],
        environment=[
            FixServer(
                name="server",
                msgclass=FixMessage,
                codec=CODEC,
                tls_config=SimpleTLSConfig(
                    cert=Path("certs/server.crt"),
                    key=Path("certs/server.key"),
                    cacert=Path("certs/rootCA.crt"),
                ),
            ),
            FixClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
                sender="TW",
                target="ISLD",
                msgclass=FixMessage,
                codec=CODEC,
                tls_config=SimpleTLSConfig(
                    cert=Path("certs/client.crt"),
                    key=Path("certs/client.key"),
                    cacert=Path("certs/rootCA.crt"),
                ),
            ),
        ],
    )
    return test
