"""FixServer driver classes."""
from typing import Optional

import select
import platform
import queue

from schema import Use

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.sockets import Codec
from testplan.common.utils.sockets.tls import TLSConfig
from testplan.common.utils.strings import slugify
from testplan.common.utils.sockets.fix.server import Server
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo

from ..base import Driver, DriverConfig


class FixServerConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.fix.server.FixServer` driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "msgclass": type,
            "codec": object,
            ConfigOption("host", default="localhost"): str,
            ConfigOption("port", default=0): Use(int),
            ConfigOption("version", default="FIX.4.2"): str,
            ConfigOption("tls_config", default=None): TLSConfig,
        }


class FixServer(Driver):
    """
    Driver for a server that can send and receive FIX messages over the session
    protocol.

    Supports multiple connections. The server stamps every outgoing message with
    the senderCompID and targetCompID for the corresponding connection.

    This is built on top of the
    :py:class:`testplan.common.utils.sockets.fix.server.Server` class, which
    provides equivalent functionality and may be used outside of MultiTest.

    NOTE: FixServer requires select.poll(), which is not implemented on all
    operating systems - typically it is available on POSIX systems but not
    on Windows.

    {emphasized_members_docs}

    :param name: Name of FixServer.
    :type name: ``str``
    :param msgclass: Type used to send and receive FIX messages.
    :type msgclass: ``type``
    :param codec: A Codec to use to encode and decode FIX messages.
    :type codec: a ``Codec`` instance
    :param host: Host name to bind to. Default: 'localhost'
    :type host: ``str``
    :param port: Port number to bind to. Default: 0 (Random port)
    :type port: ``int``
    :param version: FIX version, defaults to "FIX.4.2". This string is used
      as the contents of tag 8 (BeginString).
    :type version: ``str``
    :param tls_config: If provided the connection will be encrypted
    :type version: ``Optional[TLSConfig]``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = FixServerConfig

    def __init__(
        self,
        name: str,
        msgclass: type,
        codec: Codec,
        host: str = "localhost",
        port: int = 0,
        version: str = "FIX.4.2",
        tls_config: Optional[TLSConfig] = None,
        **options
    ):
        options.update(self.filter_locals(locals()))
        options.setdefault("file_logger", "{}.log".format(slugify(name)))

        if not hasattr(select, "poll"):
            raise RuntimeError(
                "select.poll() is required for FixServer but is not available "
                "on the current platform ({})".format(platform.system())
            )

        super(FixServer, self).__init__(**options)
        self._host: str = None
        self._port: int = None
        self._server = None

    @emphasized
    @property
    def host(self):
        """Input host provided."""
        return self._host

    @emphasized
    @property
    def port(self):
        """Port retrieved after binding."""
        return self._port

    def starting(self):
        """Starts the TCP server."""
        super(FixServer, self).starting()
        self._server = Server(
            msgclass=self.cfg.msgclass,
            codec=self.cfg.codec,
            host=self.cfg.host,
            port=self.cfg.port,
            version=self.cfg.version,
            logger=self.logger,
            tls_config=self.cfg.tls_config,
        )
        self._server.start()
        self._host = self.cfg.host
        self._port = self._server.port

        # use parent.logger here so that this goes to stdout
        # self.logger is writing to file_logger
        self.parent.logger.debug(
            "%s[%s] listening on %s:%s",
            type(self).__name__,
            self.name,
            self._host,
            self._port,
        )

    def active_connections(self):
        """
        Docstring from Server.active_connections
        """
        return self._server.active_connections()

    active_connections.__doc__ = Server.active_connections.__doc__

    def is_connection_active(self, conn_name):
        """
        Docstring from Server.is_connection_active
        """
        return self._server.is_connection_active(conn_name)

    is_connection_active.__doc__ = Server.is_connection_active.__doc__

    def send(self, msg, conn_name=(None, None)):
        """
        Docstring from Server.send
        """
        return self._server.send(msg, conn_name)

    send.__doc__ = Server.send.__doc__

    def receive(self, conn_name=(None, None), timeout=60):
        """
        Receive a FIX message from the given connection.

        The connection name defaults to ``(None, None)``. In this case,
        the server will try to find the one and only available connection. This
        will fail if there are more connections available or if the initial
        connection is no longer active.

        :param conn_name:  Connection name (sender and target ids) to receive
          message from.
        :type conn_name: ``tuple`` of ``str`` and ``str``
        :param timeout: timeout in seconds or ``None``

          - Specifying ``None`` as timeout will turn receive into a
            non-blocking call. In such case, if no message is immediately
            available, ``None`` is returned and no exception is raised.
          - Specifying a numeric value will make receive a blocking call.
            If no message is received within the timeframe, a TimeoutException
            is raised.

        :type timeout: ``int`` or ``NoneType``

        :return: received FixMessage object
        :rtype: ``FixMessage``
        """
        received = None
        timeout_info = TimeoutExceptionInfo()
        timeout_ = timeout or 0
        try:
            received = self._server.receive(conn_name, timeout=timeout_)
        except queue.Empty:
            self.logger.debug(
                "Timed out waiting for message for %s seconds", timeout_
            )
            if timeout is not None:
                raise TimeoutException(
                    "Timed out waiting for message on {0}. {1}".format(
                        self.cfg.name, timeout_info.msg()
                    )
                )

        self.logger.info(
            "Received from connection %s msg %s", conn_name, received
        )
        return received

    def flush(self):
        """
        Flush the receive queues
        """
        self._server.flush()

    def _stop_logic(self):
        if self._server:
            self._server.stop()

    def stopping(self):
        """Stops the FIX server."""
        super(FixServer, self).stopping()
        self._stop_logic()

    def aborting(self):
        """Abort logic that stops the FIX server."""
        super(FixServer, self).aborting()
        self._stop_logic()
