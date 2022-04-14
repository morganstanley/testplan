"""TCP Server module."""

import time
import socket
import select
import threading

from testplan.common.utils.timing import wait


class Server:
    """
    A server that can send and receive messages based on socket interface.
    Supports multiple connections.

    :param host: The host address the server is bound to.
    :type host: ``str``
    :param port: The port the server is bound to.
    :type port: ``str`` or ``int``
    :param listen: Socket listen argument.
    :type listen: ``int``
    """

    def __init__(self, host="localhost", port=0, listen=1):
        self._input_host = host
        self._input_port = port
        self._listen = listen
        self._ip = None
        self._port = None

        self._listening = False
        self._server = None
        self._server_thread = None

        self._lock = threading.Lock()

        self._connection_by_fd = {}
        self._fds = {}

        self.active_connections = 0
        self.accepted_connections = 0

    @property
    def host(self):
        """Input host provided."""
        return self._input_host

    @property
    def ip(self):
        """IP retrieved from socket."""
        return self._ip

    @property
    def port(self):
        """Port retrieved after binding."""
        return self._port

    @property
    def socket(self):
        """
        Returns the underlying ``socket`` object
        """
        return self._server

    def bind(self):
        """Bind to a socket."""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._input_port != 0:
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self._input_host, self._input_port))
        self._ip, self._port = self._server.getsockname()

    def serve(self, loop_sleep=0.005, listening_timeout=5):
        """Start serving connections."""
        self._server_thread = threading.Thread(
            target=self._serving, kwargs=dict(loop_sleep=loop_sleep)
        )
        self._server_thread.daemon = True
        self._server_thread.start()

        wait(lambda: self._listening, listening_timeout, raise_on_timeout=True)

    def _serving(self, loop_sleep=0.005):
        """Listen for new inbound connections."""
        self._server.listen(self._listen)
        self._listening = True

        inputs = [self._server]
        outputs = []

        while self._listening:
            try:
                readable, writable, exceptional = select.select(
                    inputs, outputs, inputs
                )
            except ValueError:
                for sock in inputs:
                    # Remove the closed socks.
                    if sock.fileno() == -1:
                        inputs.remove(sock)
                continue

            for sock in readable:
                if sock is self._server:
                    # New connection
                    conn, client_addr = sock.accept()
                    inputs.append(conn)
                    self._connection_by_fd[conn.fileno()] = conn
                    self._fds[self.active_connections] = conn.fileno()
                    self.active_connections += 1

            for sock in exceptional:
                inputs.remove(sock)
                sock.close()

            time.sleep(loop_sleep)

        self._remove_all_connections()
        try:
            self._server.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._server.close()

    def accept_connection(self, timeout=10, accept_connection_sleep=0.1):
        """
        Accepts a connection in the order in which they were received.
        Return the index of the connection, which can be used to send
        and receive messages using that connection.
        If no connection is already available or becomes available in the given
        timeout, then the method returns -1.

        :param timeout: Timeout to wait for receiving connection.
        :type timeout: ``int``
        :param accept_connection_sleep: Sleep time to retry accept connection.
        :type accept_connection_sleep: ``float``

        :return: Index of connection
        :rtype: ``int``
        """
        started = time.time()
        while True:
            if self.accepted_connections in self._fds:
                self.accepted_connections += 1
                return self.accepted_connections - 1
            if time.time() > started + timeout:
                return -1
            time.sleep(accept_connection_sleep)

    def close_connection(self, conn_idx):
        """
        Unregister, close and remove connection with given connection index

        :param conn_idx: Connection index of connection to be removed
        :type conn_idx: ``int``

        :return: ``None``
        :rtype: ``NoneType``
        """
        fdesc = self._fds[conn_idx]
        self._connection_by_fd[fdesc].close()

        del self._connection_by_fd[fdesc]
        del self._fds[conn_idx]

    def receive(
        self, size=1024, conn_idx=None, timeout=30, wait_full_size=True
    ):
        """
        Receive a message of given size (number of bytes) from the given
        connection.

        :param size: Number of bytes to receive
        :type size: ``int``
        :param conn_idx: Index of connection to receive from
        :type conn_idx: ``int``
        :param timeout: timeout in seconds
        :type timeout: ``int``
        :param wait_full_size: Wait until full size is received.
        :type wait_full_size: ``bool``

        :return: message received
        :rtype: ``bytes``
        """
        conn_idx = self._validate_connection_idx(conn_idx)

        # Get file descriptor and details of connection
        fdesc = self._fds[conn_idx]
        connection = self._connection_by_fd[fdesc]
        connection.settimeout(timeout)

        if wait_full_size is False:
            connection.settimeout(0)
            msg = connection.recv(size)
            connection.settimeout(timeout)
        else:
            with self._lock:
                msg = b""
                try:
                    while len(msg) < size:
                        new_msg = connection.recv(size - len(msg))
                        if not new_msg:
                            raise Exception("Socket connection broken")
                        msg += new_msg
                except socket.error:
                    if timeout == 0:
                        raise socket.timeout()
                    raise
        return msg

    def send(self, msg, conn_idx=None, timeout=30):
        """
        Send the given message through the given connection.

        :param msg: message to be sent
        :type msg: ``bytes``
        :param conn_idx: Index of connection to send to
        :type conn_idx: ``int``
        :param timeout: Timeout in seconds for sending all bytes
        :type timeout: ``int``

        :return: Number of bytes sent
        :rtype: ``int``
        """
        conn_idx = self._validate_connection_idx(conn_idx)

        connection = self._connection_by_fd[self._fds[conn_idx]]
        connection.settimeout(timeout)
        with self._lock:
            connection.sendall(msg)
        return len(msg)

    def close(self):
        """Closes the server and listen thread."""
        self._listening = False
        # self._serving may be stuck in select.select
        if self._server_thread:
            self._server_thread.join(timeout=0.1)

    def _validate_connection_idx(self, conn_idx):
        """
        Check if given connection index is valid.

        If this is None, then the connection defaults to the one and only
        existing active connection. If there are more active connections or the
        initial connection is no longer valid this will fail.

        :param conn_idx: Index of connection to send to
        :type conn_idx: ``int``

        :return: Connection index to send message to
        :rtype: ``int``
        """
        if conn_idx is None:
            if self.accepted_connections > 1:
                conn_idx = self.accepted_connections - 1
            else:
                conn_idx = 0

        if self.accepted_connections == 0:
            raise Exception("No connection accepted")

        if conn_idx not in self._fds:
            raise Exception("Connection {} not active".format(conn_idx))

        return conn_idx

    def _remove_all_connections(self):
        """
        Unregister, close and remove all existing connections

        :return: ``None``
        :rtype: ``NoneType``
        """
        for fdesc in self._connection_by_fd:
            self._connection_by_fd[fdesc].close()

        self._connection_by_fd = {}
        self._fds = {}
