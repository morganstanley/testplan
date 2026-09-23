"""CURVE security for the trusted pool and resource-monitor channels.

Workers in a pool share a client identity. They are trusted to execute Python;
CURVE excludes outsiders, not malicious workers. Keys live only in memory and
are delivered over child stdin (over SSH for remote workers), never argv or
logged environment assignments. The bootstrap channel must itself be trusted.
"""

import dataclasses
import json
import struct
from typing import IO, Dict

import zmq
from zmq.auth.thread import ThreadAuthenticator
from zmq.utils import z85

POOL_CHANNEL = "pool"
MONITOR_CHANNEL = "resource_monitor"
KEYS_PREFIX = b"TESTPLAN_CURVE "


@dataclasses.dataclass(frozen=True, repr=False)
class CurveClientKeys:
    """Client identity and pinned server key, encoded as Z85 strings."""

    server_public: str
    client_public: str
    client_secret: str

    def __post_init__(self) -> None:
        for key in dataclasses.astuple(self):
            try:
                if not isinstance(key, str) or len(key) != 40:
                    raise ValueError
                z85.decode(key.encode("ascii"))
            except (ValueError, KeyError, UnicodeError, struct.error):
                raise ValueError("Invalid CURVE key") from None

    def configure(self, sock: zmq.Socket) -> None:
        """Configure before connecting; never fall back to plaintext."""
        sock.curve_serverkey = self.server_public.encode("ascii")
        sock.curve_publickey = self.client_public.encode("ascii")
        sock.curve_secretkey = self.client_secret.encode("ascii")


class CurveServerKeys:
    """Per-channel keys. No sockets or threads are stored in this object.

    This can cross a multiprocessing spawn boundary. Start the authenticator
    in the process owning the socket, and stop it before destroying its context.
    """

    def __init__(self) -> None:
        if not zmq.has("curve"):
            raise RuntimeError("Testplan requires libzmq with CURVE support")
        public, self._secret = zmq.curve_keypair()
        client_public, client_secret = zmq.curve_keypair()
        self.client_keys = CurveClientKeys(
            public.decode("ascii"),
            client_public.decode("ascii"),
            client_secret.decode("ascii"),
        )

    def callback(self, domain: str, key: bytes) -> bool:
        """ZAP authorizes only this channel's worker identity."""
        return key == self.client_keys.client_public.encode("ascii")

    def start(self, sock: zmq.Socket) -> ThreadAuthenticator:
        """Secure a server socket before bind; return its owned authenticator."""
        sock.curve_server = True
        sock.curve_secretkey = self._secret
        sock.zap_domain = b"testplan"
        auth = ThreadAuthenticator(sock.context)
        auth.configure_curve_callback("testplan", credentials_provider=self)
        try:
            auth.start()
        except Exception:
            auth.stop()
            raise
        return auth


def write_curve_keys(
    stream: IO[bytes], channels: Dict[str, CurveClientKeys]
) -> None:
    """Send only client credentials and server public keys to the child."""
    payload = {
        name: dataclasses.asdict(keys) for name, keys in channels.items()
    }
    stream.write(KEYS_PREFIX + json.dumps(payload).encode("ascii") + b"\n")
    stream.flush()


def read_curve_keys(stream: IO[bytes]) -> Dict[str, CurveClientKeys]:
    """Read the private bootstrap, allowing the existing SSH prompt response."""
    line = stream.readline()
    if line.strip() == b"y":
        line = stream.readline()
    if not line.startswith(KEYS_PREFIX):
        raise ValueError("Parent did not supply CURVE credentials on stdin")
    try:
        payload = json.loads(line[len(KEYS_PREFIX) :])
        return {
            name: CurveClientKeys(**keys) for name, keys in payload.items()
        }
    except (ValueError, TypeError, AttributeError):
        # Do not include the input or parser error: both may expose secrets.
        raise ValueError("Invalid CURVE bootstrap credentials") from None
