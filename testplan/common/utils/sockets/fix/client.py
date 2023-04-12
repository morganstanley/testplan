"""Fix TCP client module."""
import ssl
import time
import socket
from typing import Optional

from testplan.common.utils.sockets.fix.utils import utc_timestamp

from .parser import tagsoverride, FixParser
from ..tls import TLSConfig


class Client:
    """
    A Basic FIX Client
    Connects to a FIX server via the FIX session protocol.
    """

    def __init__(
        self,
        msgclass,
        codec,
        host,
        port,
        sender,
        target,
        version="FIX.4.2",
        sendersub=None,
        interface=None,
        logger=None,
        tls_config: Optional[TLSConfig] = None,
    ):
        """
        Create a new FIX client.

        This constructor takes parameters that specify the address (host, port)
        to connect to and identifiers necessary to uniquely identify the
        connection (sender, target).

        :param msgclass: Type used to construct logon, logoff and received FIX
          messages.
        :type msgclass: ``type``
        :param codec: A Codec to use to encode and decode FIX messages.
        :type codec: a ``Codec`` instance
        :param host: hostname or IP address to connect to.
        :type host: ``str``
        :param port: port to connect to.
        :type port: ``str`` or ``int``
        :param sender: Value written to tag 49 (SenderCompID).
          Used to identify the firm sending the message.
        :type sender: ``str``
        :param target: Value written to tag 56 (TargetCompID).
          Used to identify the firm receiving the message.
        :type target: ``str``
        :param version: FIX version, defaults to "FIX.4.2". This string is used
          as the contents of tag 8 (BeginString).
        :type version: ``str``
        :param sendersub: Value to be used as default value tag 50
          (SenderSubID, a.k.a. OwnerID). Only used if tag 50 does not have a
          value. Used to identify the message originator.
        :type sendersub: ``str``
        :param interface: Local interface to bind to. Defaults to None, in
          which case the socket does not bind before connecting
        :type interface: (``str``, ``str`` or ``int``) tuple
        :param logger: Logger instance.
        :type logger: ``logging.Logger``
        """
        self.host = host
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if interface is not None:
            self.socket.bind(interface)

        self.version = version
        self.sender = sender
        self.target = target
        self.sendersub = sendersub
        self.in_seqno = 1
        self.out_seqno = 1
        self.timeout = 30
        self.msgclass = msgclass
        self.log_callback = logger.debug if logger else lambda msg: None
        self.tls_config = tls_config
        self.codec = codec
        self.connection_name = "{}:{}:{}_{}{}".format(
            self.sender, self.target, self.sendersub, self.host, self.port
        )

        if self.tls_config:
            self.socket = self.tls_config.get_context(
                purpose=ssl.Purpose.SERVER_AUTH
            ).wrap_socket(self.socket, server_hostname=self.host)

    @property
    def address(self):
        """
        Returns the host and port information of socket.
        """
        return self.socket.getsockname()

    def connect(self):
        """
        Transport connection.
        """
        self.log_callback(
            "Connecting socket to {}:{}".format(self.host, self.port)
        )
        return self.socket.connect((self.host, self.port))

    def sendlogon(self, custom_tags=None):
        """
        Send logon message.
        """
        req = self.msgclass.from_dict({35: "A", 98: "0", 108: "600", 141: "Y"})
        tagsoverride(req, custom_tags or {})
        if 34 in req:
            self.out_seqno = int(req[34])
        self.log_callback("Sending logon msg {}.".format(req))
        return self.send(req)

    def _populate_tags(self, msg):
        msg[8] = self.version
        msg[49] = self.sender
        msg[56] = self.target
        if 50 not in msg and self.sendersub:
            msg[50] = self.sendersub

        msg[52] = getattr(self.codec, "utc_timestamp", utc_timestamp)()

        msg[34] = self.out_seqno
        self.out_seqno += 1
        if msg[35] in (b"4", "4"):
            self.out_seqno = int(msg[36])
        return msg

    def send(self, msg):
        """
        Regular send.
        """
        return self.rawsend_tsp(self._populate_tags(msg))

    def rawsend(self, msg):
        """
        Raw send (without stamping any session tags).
        """
        return self.rawsend_tsp(msg)[1]

    def rawsend_tsp(self, msg):
        """
        Raw send (without stamping any session tags).
        """
        self.log_callback("Sending msg {}.".format(msg))

        msgstr = msg.to_wire(self.codec)

        tsp = time.time() * 1000000
        self.socket.send(msgstr)
        return tsp, msg

    def receive(self, timeout=30):
        """
        Receive a FIX message.
        """
        self.socket.settimeout(float(timeout))

        data = self.socket.recv(1)
        if not data:
            self.log_callback("Received empty data, peer closed?")
            raise socket.error("Received empty data")

        parser = FixParser()
        size = parser.consume(data)
        while size:
            size = parser.consume(self.socket.recv(size))

        self.in_seqno += 1
        return self.msgclass.from_buffer(parser.buffer, self.codec)

    def sendlogoff(self, custom_tags=None):
        """
        Send logoff message.
        """
        req = self.msgclass.from_dict({35: "5"})
        tagsoverride(req, custom_tags or {})
        self.log_callback("Sending logoff msg {}.".format(req))
        return self.send(req)

    def close(self):
        """
        Close the connection.
        """
        self.socket.close()
        self.socket = None
        self.log_callback("Closed socket.")
