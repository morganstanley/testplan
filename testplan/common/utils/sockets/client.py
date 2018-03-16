"""TCP Client module."""

import time
import socket


class Client(object):
    """
    A Basic TCP Client
    Connects to a server via the standard Session Protocol.

    To use this type:
        1. construct it
        2. connect
        3. send and/or receive
        4. close
    """
    def __init__(self, host, port, interface=None):
        """
        Create a new TCP client.
        This constructor takes parameters that specify the address (host, port)
        to connect to and an optional logging callback method.

        :param host: hostname or IP address to connect to
        :type host: ``str``
        :param port: port to connect to
        :type port: ``str`` or ``int``
        :param interface: Local interface to bind to. Defaults to None, in
            which case the socket does not bind before connecting.
        :type interface: (``str``, ``str`` or ``int``) tuple
        """
        self._input_host = host
        self._input_port = port
        self._interface = interface
        self._client = None
        self._timeout = None

    @property
    def address(self):
        """
        Returns the host and port information of socket.
        """
        return self._client.getsockname()

    def connect(self):
        """
        Connect client to socket.
        """
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._interface is not None:
            self._client.bind(self._interface)
        self._client.connect((self._input_host, self._input_port))

    def send(self, msg):
        """
        Send the given message.

        :param msg: Message to be sent.
        :type msg: ``bytes``

        :return: Timestamp when msg sent (in microseconds from epoch) and
                 number of bytes sent
        :rtype: ``tuple`` of ``long`` and ``int``
        """
        tsp = time.time() * 1000000
        size = self._client.send(msg)
        return tsp, size

    def receive(self, size, timeout=30):
        """
        Receive a message.

        :param size: Number of bytes to receive.
        :type size: ``int``
        :param timeout: Timeout in seconds.
        :type timeout: ``int``

        :return: message received
        :rtype: ``bytes``
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

    def recv(self, bufsize, flags=0):
        """
        Proxy for Python's ``socket.recv()``.

        :param bufsize: Maximum amount of data to be received at once.
        :type bufsize: ``int``
        :param flags: Defaults to zero.
        :type flags: ``int``

        :return: message received
        :rtype: ``bytes``
        """
        return self._client.recv(bufsize, flags)

    def close(self):
        """
        Close the connection.

        :return: ``None``
        :rtype: ``NoneType``
        """
        if self._client is not None:
            self._client.close()
