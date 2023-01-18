"""ZMQServer Driver."""

from schema import Use, Or
import zmq

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.timing import retry_until_timeout

from ..base import Driver, DriverConfig


class ZMQServerConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.zmq.server.ZMQServer` driver.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption("host", default="localhost"): str,
            ConfigOption("port", default=0): Use(int),
            ConfigOption("message_pattern", default=zmq.PAIR): Or(
                zmq.PAIR, zmq.REP, zmq.PUB, zmq.PUSH
            ),
        }


class ZMQServer(Driver):
    """
    The ZMQServer can receive multiple connections from different ZMQClients.
    The socket can be of type:

        * zmq.PAIR
        * zmq.REP
        * zmq.PUB
        * zmq.PUSH

    {emphasized_members_docs}

    :param name: Name of ZMQServer.
    :type name: ``str``
    :param host: Host name to bind to. Default: 'localhost'
    :type host: ``str``
    :param port: Port number to bind to. Default: 0 (Random port)
    :type port: ``int``
    :param message_pattern: Message pattern. Default: ``zmq.PAIR``
    :type message_pattern: ``int``
    """

    CONFIG = ZMQServerConfig

    def __init__(
        self,
        name: str,
        host: str = "localhost",
        port: int = 0,
        message_pattern=zmq.PAIR,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(ZMQServer, self).__init__(**options)
        self._host: str = None
        self._port: int = None
        self._zmq_context = None
        self._socket = None

    @emphasized
    @property
    def host(self):
        """Target host name."""
        return self._host

    @emphasized
    @property
    def port(self):
        """Port number assigned."""
        return self._port

    @property
    def socket(self):
        """
        Returns the underlying ``zmq.sugar.socket.Socket`` object.
        """
        return self._socket

    def send(self, data, timeout=30):
        """
        Try to send the message until it either sends or hits timeout.

        :param timeout: Timeout to retry sending the message
        :type timeout: ``int``
        """
        return retry_until_timeout(
            exception=zmq.ZMQError,
            item=self._socket.send,
            kwargs={"data": data, "flags": zmq.NOBLOCK},
            timeout=timeout,
            raise_on_timeout=True,
        )

    def receive(self, timeout=30):
        """
        Try to send the message until it either has been received or
        hits timeout.

        :param timeout: Timeout to retry receiving the message
        :type timeout: ``int``

        :return: The received message
        :rtype: ``object`` or ``str`` or ``zmq.sugar.frame.Frame``
        """
        return retry_until_timeout(
            exception=zmq.ZMQError,
            item=self._socket.recv,
            kwargs={"flags": zmq.NOBLOCK},
            timeout=timeout,
            raise_on_timeout=True,
        )

    def starting(self):
        """
        Start the ZMQServer.
        """
        super(ZMQServer, self).starting()
        # pylint: disable=abstract-class-instantiated
        self._zmq_context = zmq.Context()
        self._socket = self._zmq_context.socket(self.cfg.message_pattern)
        if self.cfg.port == 0:
            port = self._socket.bind_to_random_port(
                "tcp://{host}".format(host=self.cfg.host)
            )
        else:
            self._socket.bind(
                "tcp://{host}:{port}".format(
                    host=self.cfg.host, port=self.cfg.port
                )
            )
            port = self.cfg.port
        self._host = self.cfg.host
        self._port = port

    def stopping(self):
        """
        Stop the ZMQServer.
        """
        super(ZMQServer, self).stopping()
        if not self._socket.closed:
            self._socket.close()
        if not self._zmq_context.closed:
            self._zmq_context.term()

    def aborting(self):
        """Abort logic that stops the server."""
        if not self._socket.closed:
            self._socket.close()
        if not self._zmq_context.closed:
            self._zmq_context.term()
