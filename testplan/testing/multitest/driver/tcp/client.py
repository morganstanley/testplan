"""TCPClient driver classes."""

import socket

from schema import Use, Or

from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo
from testplan.common.config import ConfigOption
from testplan.common.utils.context import is_context, expand
from testplan.common.utils.sockets import Client

from ..base import Driver, DriverConfig


class TCPClientConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.tcp.client.TCPClient` driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            'host': Or(str,
                       lambda x: is_context(x)),
            'port': Or(Use(int), lambda x: is_context(x)),
            ConfigOption('interface', default=None): tuple,
            ConfigOption('connect_at_start', default=True): bool
        }


class TCPClient(Driver):
    """
    TCP client driver.

    This is built on top of the
    :py:class:`testplan.common.utils.sockets.client.Client` class, which
    provides equivalent functionality and may be used outside of MultiTest.

    :param host: Target host name. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type host: ``str``
    :param port: Target port number. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type port: ``int``
    :param interface: Interface to bind to.
    :type interface: ``tuple``(``str, ``int``)
    :param connect_at_start: Connect to server on start. Default: True
    :type connect_at_start: ``bool``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver`` options.
    """

    CONFIG = TCPClientConfig

    def __init__(self, **options):
        super(TCPClient, self).__init__(**options)
        self._host = None
        self._port = None
        self._client = None

    @property
    def host(self):
        """Target host name."""
        return self._host

    @property
    def port(self):
        """Client port number assigned."""
        return self._port

    def connect(self):
        """
        Connect client.
        """
        self._client.connect()
        self._host, self._port = self._client.address

    def send_text(self, msg, standard='utf-8'):
        """
        Encodes to bytes and calls
        :py:meth:`TCPClient.send <testplan.testing.multitest.driver.tcp.client.TCPClient.send>`.
        """
        return self.send(bytes(msg.encode(standard)))

    def send(self, msg):
        """
        Sends bytes.

        :param msg: Message to be sent
        :type msg: ``bytes``

        :return: Number of bytes sent
        :rtype: ``int``
        """
        return self._client.send(msg)[1]

    def send_tsp(self, msg):
        """
        Sends bytes and returns also timestamp sent.

        :param msg: Message to be sent
        :type msg: ``bytes``

        :return: Timestamp when msg sent (in microseconds from epoch)
                 and number of bytes sent
        :rtype: ``tuple`` of ``long`` and ``int``
        """
        return self._client.send(msg)

    def receive_text(self, standard='utf-8', **kwargs):
        """
        Calls
        :py:meth:`TCPClient.receive <testplan.testing.multitest.driver.tcp.server.TCPClient.receive>`
        and decodes received bytes.
        """
        return self.receive(**kwargs).decode(standard)

    def receive(self, size=1024, timeout=30):
        """Receive bytes from the given connection."""
        received = None
        timeout_info = TimeoutExceptionInfo()
        try:
            received = self._client.receive(size, timeout=timeout or 0)
        except socket.timeout:
            if timeout is not None:
                raise TimeoutException(
                    'Timed out waiting for message on {0}. {1}'.format(
                        self.cfg.name, timeout_info.msg()))
        return received

    def reconnect(self):
        """Client reconnect."""
        self._client.close()
        self.connect()

    def starting(self):
        """Start the TCP client and optionally connect to host/post."""
        super(TCPClient, self).starting()
        server_host = expand(self.cfg.host, self.context)
        server_port = expand(self.cfg.port, self.context, int)
        self._client = Client(host=server_host, port=server_port)
        if self.cfg.connect_at_start:
            self.connect()

    def stopping(self):
        """Close the client connection."""
        super(TCPClient, self).stopping()
        if self._client:
            self._client.close()

    def aborting(self):
        """Abort logic that stops the client."""
        if self._client:
            self._client.close()
