"""TCPClient driver classes."""

import socket
from typing import Union, Tuple, Optional

from schema import Or
from testplan.common.utils import networking
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo
from testplan.common.config import ConfigOption
from testplan.common.utils.context import expand, ContextValue
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
            "host": Or(str, ContextValue),
            "port": Or(int, str, ContextValue),
            ConfigOption("interface", default=None): Or(None, tuple),
            ConfigOption("connect_at_start", default=True): bool,
        }


class TCPClient(Driver):
    """
    TCP client driver.

    This is built on top of the
    :py:class:`testplan.common.utils.sockets.client.Client` class, which
    provides equivalent functionality and may be used outside of MultiTest.

    {emphasized_members_docs}

    :param name: Name of TCPClient.
    :param host: Target host name. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :param port: Target port number. This can be a
        :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :param interface: Interface to bind to.
    :param connect_at_start: Connect to server on start. Default: True

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = TCPClientConfig

    def __init__(
        self,
        name: str,
        host: Union[str, ContextValue],
        port: Union[int, str, ContextValue],
        interface: Union[Tuple[str, int], None] = None,
        connect_at_start: bool = True,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(TCPClient, self).__init__(**options)
        self._host: Optional[str] = None
        self._port: Optional[int] = None
        self._client = None
        self._server_host = None
        self._server_port = None

    @property
    def host(self) -> str:
        """Target host name."""
        return self._host

    @property
    def port(self) -> int:
        """Client port number assigned."""
        return self._port

    @property
    def server_port(self) -> int:
        return self._server_port

    def connect(self) -> None:
        """
        Connect client.
        """
        self._client.connect()
        self._host, self._port = self._client.address

    def send_text(self, msg: str, standard: str = "utf-8") -> int:
        """
        Encodes to bytes and calls
        :py:meth:`TCPClient.send
        <testplan.testing.multitest.driver.tcp.client.TCPClient.send>`.
        """
        return self.send(msg.encode(standard))

    def send(self, msg: bytes) -> int:
        """
        Sends bytes.

        :param msg: Message to be sent

        :return: Number of bytes sent
        """
        return self._client.send(msg)[1]

    def send_tsp(self, msg: bytes) -> Tuple[float, int]:
        """
        Sends bytes and returns also timestamp sent.

        :param msg: Message to be sent

        :return: Timestamp when msg sent (in microseconds from epoch)
                 and number of bytes sent
        """
        return self._client.send(msg)

    def receive_text(self, standard: str = "utf-8", **kwargs) -> str:
        """
        Calls
        :py:meth:`TCPClient.receive
        <testplan.testing.multitest.driver.tcp.server.TCPClient.receive>`
        and decodes received bytes.
        """
        return self.receive(**kwargs).decode(standard)

    def receive(self, size: int = 1024, timeout: int = 30) -> Optional[bytes]:
        """Receive bytes from the given connection."""
        received = None
        timeout_info = TimeoutExceptionInfo()
        try:
            received = self._client.receive(size, timeout=timeout or 0)
        except socket.timeout:
            if timeout is not None:
                raise TimeoutException(
                    "Timed out waiting for message on {0}. {1}".format(
                        self.cfg.name, timeout_info.msg()
                    )
                )
        return received

    def reconnect(self) -> None:
        """Client reconnect."""
        self.close()
        self.connect()

    def starting(self) -> None:
        """Start the TCP client and optionally connect to host/post."""
        super(TCPClient, self).starting()
        self._server_host = expand(self.cfg.host, self.context)
        self._server_port = networking.port_to_int(
            expand(self.cfg.port, self.context)
        )
        self._client = Client(
            host=self._server_host,
            port=self._server_port,
            interface=self.cfg.interface,
        )
        if self.cfg.connect_at_start:
            self.connect()

    def stopping(self) -> None:
        """Close the client connection."""
        super(TCPClient, self).stopping()
        self.close()

    def close(self) -> None:
        """
        Close connection.
        """
        if self._client:
            self._client.close()

    def aborting(self) -> None:
        """Abort logic that stops the client."""
        self.close()
