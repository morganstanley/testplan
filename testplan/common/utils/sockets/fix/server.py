"""Fix TCP server module."""

import errno
import socket
import ssl
from typing import Optional

import select
import threading
import queue

from testplan.common.utils.sockets.fix.parser import FixParser
from testplan.common.utils.sockets.tls import TLSConfig
from testplan.common.utils.timing import (
    TimeoutException,
    TimeoutExceptionInfo,
    wait,
)
from testplan.common.utils.sockets.fix.utils import utc_timestamp


class ConnectionDetails:
    """
    Contains all information required for each connection to the server
    """

    def __init__(
        self, connection, name=None, queue=None, in_seqno=1, out_seqno=1
    ):
        """
        Create a new ConnectionDetails. Only the connection is required
        initially, as the rest of the details are set later.

        :param connection: The connection
        :type connection: ``socket._socketobject``
        :param name: Name of connection (tuple of sender and target)
        :type name: ``tuple`` of ``str`` and ``str``
        :param queue: Queue of receiving messages
        :type queue: ``queue``
        :param in_seqno: Input messages sequence number
        :type in_seqno: ``int``
        :param out_seqno: Output messages sequence number
        :type out_seqno: ``int``
        """
        self.connection = connection
        self.name = name
        self.queue = queue
        self.in_seqno = in_seqno
        self.out_seqno = out_seqno


def _has_logon_tag(msg):
    """
    Check if it is a logon message.

    :param msg: Fix message
    :type msg: ``FixMessage``

    :return: ``True`` if it is a logon message
    :rtype: ``bool``
    """
    return msg.tag_exact(35, "A")


def _is_session_control_msg(msg):
    """
    Check if message is logout or heartbeat.

    :param msg: Fix message.
    :type msg: ``FixMessage``

    :return: ``True`` if it is a message with non-business code
    :rtype: ``bool``
    """
    return _has_logout_tag(msg) or _has_heartbeat_tag(msg)


def _has_logout_tag(msg):
    """
    Check if logout message.

    :param msg: Fix message.
    :type msg: ``FixMessage``

    :return: True if it is a logout message
    :rtype: ``bool``
    """
    return msg.tag_exact(35, "5")


def _has_heartbeat_tag(msg):
    """
    Check if heartbeat message.

    :param msg: Fix message.
    :type msg: ``FixMessage``

    :return: True if it is a heartbeat message
    :rtype: ``bool``
    """
    return msg.tag_exact(35, "0")


class Server:
    """
    A server that can send and receive FIX messages over the FIX session protocol.
    Supports multiple connections.

    The server stamps every outgoing message with the senderCompID and
    targetCompID for the corresponding connection.
    """

    def __init__(
        self,
        msgclass,
        codec,
        host="localhost",
        port=0,
        version="FIX.4.2",
        logger=None,
        tls_config: Optional[TLSConfig] = None,
    ):
        """
        Create a new FIX server.

        This constructor takes parameters that specify the address (host, port)
        to bind to. The server stamps every outgoing message with the
        senderCompID and targetCompID for the corresponding connection.

        :param msgclass: Type used to send and receive FIX messages.
        :type msgclass: ``type``
        :param codec: A Codec to use to encode and decode FIX messages.
        :type codec: a ``Codec`` instance
        :param host: hostname or IP address to bind to.
        :type host: ``str``
        :param port: port number
        :type port: ``str`` or ``int``
        :param version: FIX version, defaults to "FIX.4.2". This string is used
          as the contents of tag 8 (BeginString).
        :type version: ``str``

        :param logger: Logger instance to be used.
        :type logger: ``logging.Logger``
        """
        self._input_host = host
        self._input_port = port
        self._ip = None
        self._port = None
        self.version = version
        self.msgclass = msgclass
        self.codec = codec
        self.log_callback = logger.debug if logger else lambda msg: None
        self.tls_config = tls_config

        self._listening = False

        self._conndetails_by_fd = {}
        self._conndetails_by_name = {}
        self._first_sender = None
        self._first_target = None

        self._socket: socket.socket = None
        self._recv_thread = None
        self._lock = threading.Lock()
        self._pobj = select.poll()
        self._ssl_context: ssl.SSLContext = (
            self.tls_config.get_context(purpose=ssl.Purpose.CLIENT_AUTH)
            if self.tls_config
            else None
        )

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

    def start(self, timeout=30):
        """
        Start the FIX server.
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._socket.bind((self._input_host, self._input_port))
        self._ip, self._port = self._socket.getsockname()

        self.log_callback(
            "Started server on {}:{}".format(self.host, self.port)
        )

        self._recv_thread = threading.Thread(target=self._listen)
        self._recv_thread.daemon = True
        self._recv_thread.start()

        timeout_info = TimeoutExceptionInfo()
        wait(lambda: self._listening, timeout=timeout, interval=0.1)

        if not self._listening:
            raise TimeoutException(
                "Could not start server: timed out on listening. {}".format(
                    timeout_info.msg()
                )
            )

        self.log_callback("Listening for socket events.")

    def _listen(self):
        """
        Listen for new inbound connections and messages from existing
        connections.
        """
        self._socket.listen(1)
        self._listening = True

        self._pobj.register(
            self._socket.fileno(),
            select.POLLIN | select.POLLNVAL | select.POLLHUP,
        )

        closed = False
        while (not closed) and self._listening:
            events = self._pobj.poll(1.0)
            for fdesc, event in events:
                if fdesc == self._socket.fileno():
                    # Socket event received
                    if event in [select.POLLNVAL, select.POLLHUP]:
                        self.log_callback('"Close socket" event received.')
                        closed = True
                        break  # out of 'for'
                    elif event == select.POLLIN:
                        self.log_callback('"New connection" event received.')
                        self._add_connection()
                    else:
                        raise Exception(
                            "Unexpected event {0} on fdesc {1}.".format(
                                event, fdesc
                            )
                        )
                else:
                    # Connection event received
                    self._process_connection_event(fdesc, event)

        self._remove_all_connections()
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def _add_connection(self):
        """
        Accept new inbound connection from socket.
        """
        connection, _ = self._socket.accept()
        if self._ssl_context is not None:
            connection = self._ssl_context.wrap_socket(
                connection, server_side=True
            )
        conn_details = ConnectionDetails(connection)
        self._conndetails_by_fd[connection.fileno()] = conn_details
        self._pobj.register(
            connection.fileno(),
            select.POLLIN | select.POLLNVAL | select.POLLHUP,
        )

    def _remove_connection(self, fdesc):
        """
        Unregister, close and remove inbound connection with given fd.

        :param fdesc: File descriptor of connection to be removed.
        :type fdesc: ``int``
        """
        self._pobj.unregister(fdesc)
        try:
            self._conndetails_by_fd[fdesc].connection.shutdown(
                socket.SHUT_RDWR
            )
        except socket.error as serr:
            if serr.errno != errno.ENOTCONN:
                raise
                # Else, client already closed the connection.
        self._conndetails_by_fd[fdesc].connection.close()

        name = self._conndetails_by_fd[fdesc].name
        del self._conndetails_by_fd[fdesc]
        self._conndetails_by_name.pop(name, None)

    def _remove_all_connections(self):
        """
        Unregister, close and remove all existing inbound connections.
        """
        for fdesc in self._conndetails_by_fd:
            self._pobj.unregister(fdesc)
            self._conndetails_by_fd[fdesc].connection.shutdown(
                socket.SHUT_RDWR
            )
            self._conndetails_by_fd[fdesc].connection.close()

            self._conndetails_by_name.pop(
                self._conndetails_by_fd[fdesc].name, None
            )
        self._conndetails_by_fd = {}

    def _process_connection_event(self, fdesc, event):
        """
        Process an event received from a connection.

        :param fdesc: File descriptor of the connection the message was
          received from.
        :type fdesc: ``int``
        :param event: Event received from connection.
        :type event: ``.int``
        """
        connection = self._conndetails_by_fd[fdesc].connection
        if event == select.POLLIN:
            with self._lock:
                data = connection.recv(1)
                if not data:
                    self.log_callback(
                        "Closing connection {} since no data available".format(
                            self._conndetails_by_fd[fdesc].name
                        )
                    )
                    self._remove_connection(fdesc)
                else:
                    msg = self._parse_data(data, connection)
                    self._process_message(fdesc, msg)

        elif event in [select.POLLNVAL, select.POLLHUP]:
            self.log_callback(
                "Closing connection {} event received".format(connection.name)
            )
            self._remove_connection(fdesc)
        else:
            raise Exception(
                "unexpected event {0} on fdesc {1}".format(event, fdesc)
            )

    def _parse_data(self, data, connection):
        """
        Parse FIX message received from connection

        :param data: First part of data received from connection
        :type data: ``str``
        :param connection: Connection to read from
        :type connection: ``socket._socketobject``

        :return: Fix msg received
        :rtype: ``ms.fix.FixMessage``
        """
        parser = FixParser()
        size = parser.consume(data)
        while size:
            size = parser.consume(connection.recv(size))
        return self.msgclass.from_buffer(parser.buffer, self.codec)

    def _process_message(self, fdesc, msg):
        """
        Process given message received from connection with given fd.

        :param fdesc: File descriptor of connection message was received from.
        :type fdesc: ``int``
        :param msg: Fix message received.
        :type msg: ``FixMessage``
        """
        conn_name = (msg[56], msg[49])

        if _has_logout_tag(msg):
            self._no_lock_send(msg, conn_name, fdesc)
            self._remove_connection(fdesc)
        elif self._conn_loggedon(conn_name):
            if _is_session_control_msg(msg):
                self.log_callback(
                    "Session control msg from {}".format(conn_name)
                )
                self._no_lock_send(msg, conn_name)
            else:
                self.log_callback(
                    "Incoming data msg from {}".format(conn_name)
                )
                self._conndetails_by_name[conn_name].in_seqno += 1
                self._conndetails_by_name[conn_name].queue.put(msg, True, 1)
        elif _has_logon_tag(msg):
            self._logon_connection(fdesc, conn_name)
            self._no_lock_send(msg, conn_name)
        else:
            raise Exception(
                "Connection {} sent msg before logon".format(conn_name)
            )

    def _conn_loggedon(self, conn_name):
        """
        Check if given connection is logged on.

        :param conn_name: Connection name.
        :type conn_name: ``tuple`` of ``str`` and ``str``

        :return: ``True`` if it is a connection has already logged on
        :rtype: ``bool``
        """
        return conn_name in self._conndetails_by_name

    def _logon_connection(self, fdesc, conn_name):
        """
        Logon given connection for given file descriptor.

        :param fdesc: File descriptor of connection.
        :type fdesc: ``int``
        :param conn_name: Connection name.
        :type conn_name: ``tuple`` of ``str`` and ``str``
        """
        conndetails = self._conndetails_by_fd[fdesc]
        conndetails.name = conn_name
        conndetails.queue = queue.Queue()
        conndetails.in_seqno = 1
        conndetails.out_seqno = 1
        self._conndetails_by_name[conn_name] = conndetails
        if self._first_sender is None:
            (self._first_sender, self._first_target) = conn_name
        self.log_callback("Logged on connection {}.".format(conn_name))

    def active_connections(self):
        """
        Returns a list of currently active connections

        :return: List of active connection names (each a tuple of sender and
          target)
        :rtype: ``list`` of ``tuple`` of ``str`` and ``str``
        """

        return [
            detail.name
            for detail in self._conndetails_by_fd.values()
            if detail.name is not None
        ]

    def is_connection_active(self, conn_name):
        """
        Checks whether the given connection is currently active.

        :param conn_name: Connection name to be checked if active
        :type conn_name: ``tuple`` of ``str`` and ``str``

        :return: ``True`` if the given connection is active. ``False`` otherwise
        :rtype: ``bool``
        """
        return conn_name in self._conndetails_by_name

    def stop(self):
        """
        Close the connection.
        """
        self._listening = False
        if self._recv_thread:
            self._recv_thread.join()
        self.log_callback("Stopped server.")

    def _validate_connection_name(self, conn_name):
        """
        Check if given connection name is valid.

        If this is ``(None, None)``, then the connection defaults to the one
        and only existing active connection. If there are more active
        connections or the initial connection is no longer valid this will fail.

        The tuple of ``(sender, target)`` represents the connection name.

        :param sender: Sender id.
        :type sender: ``str``
        :param target: Target id.
        :type target: ``str``

        :return: Connection name to send message to.
        :rtype: ``tuple`` of ``str`` and ``str``
        """
        sender, target = conn_name
        if (sender, target) == (None, None):
            active = len(self._conndetails_by_name)
            if active != 1:
                raise Exception(
                    "Cannot use default connection - "
                    "{} connection(s) active, expect 1".format(active)
                )
            (sender, target) = (self._first_sender, self._first_target)

        if not self.is_connection_active((sender, target)):
            raise Exception(
                "Connection {} not active".format((sender, target))
            )

        return sender, target

    def _add_msg_tags(self, msg, conn_name, fdesc=None):
        """
        Add session tags and senderCompID and targetCompID tags to the given
        FIX message.

        :param msg: Message to be sent.
        :type msg: ``FixMessage``
        :param sender: Sender id.
        :type sender: ``str``
        :param target: Target id.
        :type target: ``str``

        :return: The FIX msg with the tags set.
        :rtype: ``FixMessage``
        """
        sender, target = conn_name
        msg[8] = self.version
        if fdesc:
            conndetails = self._conndetails_by_fd[fdesc]
        else:
            conndetails = self._conndetails_by_name[(sender, target)]
        msg[34] = conndetails.out_seqno
        conndetails.out_seqno += 1
        msg[49] = sender
        msg[56] = target
        msg[52] = getattr(self.codec, "utc_timestamp", utc_timestamp)()
        return msg

    def _no_lock_send(self, msg, conn_name, fdesc=None):
        """
        Send the given Fix message through the given connection, expecting
        the lock is already acquired.

        The message will be enriched with session tags and sequence numbers.

        :param msg: message to be sent
        :type msg: ``FixMessage``
        :param sender: Sender id.
        :type sender: ``str``
        :param target: Target id.
        :type target: ``str``
        """
        sender, target = conn_name
        msg = self._add_msg_tags(msg, (sender, target), fdesc)
        self.log_callback(
            "Sending on connection {} message {}".format((sender, target), msg)
        )
        if fdesc:
            self._conndetails_by_fd[fdesc].connection.send(
                msg.to_wire(self.codec)
            )
        else:
            self._conndetails_by_name[(sender, target)].connection.send(
                msg.to_wire(self.codec)
            )

    def send(self, msg, conn_name=(None, None)):
        """
        Send the given Fix message through the given connection.

        The message will be enriched with session tags and sequence numbers.
        The connection name - (sender, target) - defaults to (None, None).
        In this case, the server will try to find the one and only available
        connection. This will fail if there are more connections available or
        if the initial connection is no longer active.

        :param msg: Message to be sent.
        :type msg: ``FixMessage``
        :param conn_name: Connection name to send message to. This is the tuple
          (sender id, target id)
        :type conn_name: ``tuple`` of ``str`` and ``str``

        :return: Fix message sent
        :rtype: ``FixMessage``
        """
        conn_name = self._validate_connection_name(conn_name)
        with self._lock:
            conn_name = self._validate_connection_name(conn_name)
            msg = self._add_msg_tags(msg, conn_name)
            self.log_callback(
                "Sending on connection {} message {}".format(conn_name, msg)
            )
            conn_name = self._validate_connection_name(conn_name)
            self._conndetails_by_name[conn_name].connection.send(
                msg.to_wire(self.codec)
            )
        return msg

    def receive(self, conn_name=(None, None), timeout=30):
        """
        Receive a FIX message from the given connection.

        The connection name defaults to ``(None, None)``. In this case,
        the server will try to find the one and only available connection.
        This will fail if there are more connections available or if the initial
        connection is no longer active.

        :param conn_name: Connection name to receive message from
        :type conn_name: ``tuple`` of ``str`` and ``str``
        :param timeout: timeout in seconds
        :type timeout: ``int``

        :return: Fix message received
        :rtype: ``FixMessage``
        """
        conn_name = self._validate_connection_name(conn_name)
        return self._conndetails_by_name[conn_name].queue.get(True, timeout)

    def flush(self):
        """
        Flush the receive queues.
        """
        for conn in self._conndetails_by_name:
            self._flush_queue(self._conndetails_by_name[conn].queue)
        if self.log_callback:
            self.log_callback("Flushed received message queues")

    def _flush_queue(self, msg_queue):
        """
        Flush the given receive queue.

        :param msg_queue: Queue to flush.
        :type msg_queue: ``queue``
        """
        try:
            while True:
                msg_queue.get(False)
        except queue.Empty:
            return
