"""TCP Client module."""

import time
import socket
from typing import Union, Tuple


class Client:
    """
    A Basic TCP Client that connects to a server via socket interface.

    To use this type:

        1. construct it
        2. connect
        3. send and/or receive
        4. close
    """

    def __init__(
        self,
        host: str,
        port: Union[str, int],
        interface: Union[Tuple[str, int], None] = None,
    ) -> None:
        """
        Create a new TCP client.
        This constructor takes parameters that specify the address (host, port)
        to connect to and an optional logging callback method.

        :param host: hostname or IP address to connect to
        :param port: port to connect to
        :param interface: Local interface to bind to. Defaults to None, in
            which case the socket does not bind before connecting.
        """
        self._input_host = host
        self._input_port = port
        self._interface = interface
        self._client = None
        self._timeout = None

    @property
    def address(self) -> Tuple[str, int]:
        """
        Returns the host and port information of socket.
        """
        return self._client.getsockname()

    @property
    def port(self) -> Union[str, int]:
        return self._input_port

    def connect(self) -> None:
        """
        Connect client to socket.
        """
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._interface:
            self._client.bind(self._interface)
        self._client.connect((self._input_host, self._input_port))

    def send(self, msg: bytes) -> Tuple[float, int]:
        """
        Send the given message.

        :param msg: Message to be sent.
        :return: Timestamp when msg sent (in microseconds from epoch) and
                 number of bytes sent
        """
        tsp = time.time() * 1000000
        size = self._client.send(msg)
        return tsp, size

    def receive(self, size: int, timeout: int = 30) -> bytes:
        """
        Receive a message.

        :param size: Number of bytes to receive.
        :param timeout: Timeout in seconds.
        :return: message received
        """
        if timeout != self._timeout:
            self._timeout = timeout
        self._client.settimeout(timeout)
        try:
            msg = self._client.recv(size)
        except Exception:
            if timeout == 0:
                raise socket.timeout
            raise
        return msg

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        """
        Proxy for Python's ``socket.recv()``.

        :param bufsize: Maximum amount of data to be received at once.
        :param flags: Defaults to zero.
        :return: message received
        """
        return self._client.recv(bufsize, flags)

    def close(self) -> None:
        """
        Close the connection.
        """
        if self._client is not None:
            self._client.close()
