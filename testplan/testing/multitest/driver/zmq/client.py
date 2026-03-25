"""ZMQClient Driver."""

from typing import Any, Dict, List, Optional, Union

from schema import Or
import zmq

from testplan.common.config import ConfigOption
from testplan.common.utils.context import ContextValue, expand
from testplan.common.utils.convert import make_iterables
from testplan.common.utils.timing import retry_until_timeout

from ..base import (
    Driver,
    DriverConfig,
)
from ..connection import (
    BaseConnectionInfo,
    Direction,
    Protocol,
    PortConnectionInfo,
)


class ZMQClientConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.zmq.client.ZMQClient` driver.
    """

    @classmethod
    def get_options(cls) -> Dict[Any, Any]:
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "hosts": Or(*make_iterables([str, ContextValue])),
            "ports": Or(*make_iterables([int, ContextValue])),
            ConfigOption("message_pattern", default=zmq.PAIR): Or(
                zmq.PAIR, zmq.REQ, zmq.SUB, zmq.PULL
            ),
            ConfigOption("connect_at_start", default=True): bool,
        }


class ZMQClient(Driver):
    """
    The ZMQClient can make multiple connections to different ZMQServers. The
    socket can be of type:

      * zmq.PAIR
      * zmq.REQ
      * zmq.SUB
      * zmq.PULL

    {emphasized_members_docs}

    :param name: Name of ZMQClient.
    :type name: ``str``
    :param hosts: List of ZMQServer hostnames to connect to. These can be
        :py:class:`~testplan.common.utils.context.ContextValue` objects
        and will be expanded on runtime.
    :type hosts: ``list`` of ``str``
    :param ports: List of ZMQServer ports to connect to. These can be
        :py:class:`~testplan.common.utils.context.ContextValue` objects
        and will be expanded on runtime. The port correspond to the host
        at the same index.
    :type ports: ``list`` of ``int``
    :param message_pattern: Type of socket to create connection with. It can
      be zmq.PAIR (0), zmq.REQ (3), zmq.SUB (2) or zmq.PULL (7).
    :type message_pattern: ``int``
    :param connect_at_start: If True the socket connects immediately after
      starting the ZMQClient.
    """

    CONFIG = ZMQClientConfig

    def __init__(
        self,
        name: str,
        hosts: Union[List[Union[str, ContextValue]], str, ContextValue],
        ports: Union[List[Union[int, ContextValue]], int, ContextValue],
        message_pattern: int = zmq.PAIR,
        connect_at_start: bool = True,
        **options: Any,
    ) -> None:
        options.update(self.filter_locals(locals()))
        super(ZMQClient, self).__init__(**options)
        self._hosts: List[str] = []
        self._ports: List[str] = []
        self._zmq_context: Optional[zmq.Context[Any]] = None
        self._socket: Optional[zmq.Socket[Any]] = None

    @property
    def hosts(self) -> List[str]:
        """Hosts client connects to."""
        return self._hosts

    @property
    def ports(self) -> List[str]:
        """Ports of the associated hosts."""
        return self._ports

    def connect(self) -> None:
        """
        Connect the client socket to all configured connections.
        """
        if self._socket is None:
            raise RuntimeError("self._socket must not be None")
        for i, host in enumerate(self.cfg.hosts):
            self._hosts.append(expand(host, self.context))
            self._ports.append(expand(self.cfg.ports[i], self.context, int))
            self._socket.connect(
                "tcp://{host}:{port}".format(
                    host=self._hosts[i], port=self._ports[i]
                )
            )

    def disconnect(self) -> None:
        """
        Disconnect the client socket from all configured connections if still
        connected.
        """
        if self._socket is None or self._socket.closed:
            return
        for i, host in enumerate(self._hosts):
            try:
                self._socket.disconnect(
                    "tcp://{host}:{port}".format(
                        host=host, port=self._ports[i]
                    )
                )
            except zmq.ZMQError as exc:
                if str(exc) != "No such file or directory":
                    raise exc

    def reconnect(self) -> None:
        """
        Disconnect and reconnect the client.
        """
        self.disconnect()
        self.connect()

    def send(self, data: Any, timeout: int = 30) -> Any:
        """
        Try to send the message until it either sends or hits timeout.

        :param data: The content of the message.
        :type data: ``bytes`` or ``zmq.sugar.frame.Frame`` or ``memoryview``
        :param timeout: Timeout to retry sending the message.
        :type timeout: ``int``

        :return: ``None``
        :rtype: ``NoneType``
        """
        if self._socket is None:
            raise RuntimeError("self._socket must not be None")
        return retry_until_timeout(
            exception=zmq.ZMQError,
            item=self._socket.send,
            kwargs={"data": data, "flags": zmq.NOBLOCK},
            timeout=timeout,
            raise_on_timeout=True,
        )

    def receive(self, timeout: int = 30) -> Any:
        """
        Try to receive the message until it has either been received or
        hits timeout.

        :param timeout: Timeout to retry receiving the message.
        :type timeout: ``int``

        :return: The received message.
        :rtype: ``bytes`` or ``zmq.sugar.frame.Frame`` or ``memoryview``
        """
        if self._socket is None:
            raise RuntimeError("self._socket must not be None")
        return retry_until_timeout(
            exception=zmq.ZMQError,
            item=self._socket.recv,
            kwargs={"flags": zmq.NOBLOCK},
            timeout=timeout,
            raise_on_timeout=True,
        )

    def subscribe(self, topic_filter: Any) -> None:
        """
        Subscribe the client to receive messages where the prefix of the
        message matches the topic filter. Only for SUBSCRIBE clients.

        :param topic_filter: String to filter received messages by.
        :type topic_filter: ``str``
        """
        if self.cfg.message_pattern == zmq.SUB:
            if self._socket is None:
                raise RuntimeError("self._socket must not be None")
            self._socket.setsockopt(zmq.SUBSCRIBE, topic_filter)

    def unsubscribe(self, topic_filter: Any) -> None:
        """
        Unsubscribe the client from a particular filter. Only for
        SUBSCRIBE clients.

        :param topic_filter: Filter to be removed.
        :type topic_filter: ``str``
        """
        if self.cfg.message_pattern == zmq.SUB:
            if self._socket is None:
                raise RuntimeError("self._socket must not be None")
            self._socket.setsockopt(zmq.UNSUBSCRIBE, topic_filter)

    def starting(self) -> None:
        """
        Start the ZMQ client.
        """
        super(ZMQClient, self).starting()
        # pylint: disable=abstract-class-instantiated
        self._zmq_context = zmq.Context()
        self._socket = self._zmq_context.socket(self.cfg.message_pattern)
        if self.cfg.connect_at_start:
            self.connect()

    def stopping(self) -> None:
        """
        Stop the ZMQ client.
        """
        super(ZMQClient, self).stopping()
        if self._socket is not None and not self._socket.closed:
            self._socket.close()
        if self._zmq_context is not None and not self._zmq_context.closed:
            self._zmq_context.term()

    def aborting(self) -> None:
        """Abort logic that stops the client."""
        if self._socket is not None and not self._socket.closed:
            self._socket.close()
        if self._zmq_context is not None and not self._zmq_context.closed:
            self._zmq_context.term()

    def flush(self) -> None:
        """
        Flush the clients queue of messages by reconnecting.
        """
        self.reconnect()

    def get_connections(self) -> List[BaseConnectionInfo]:
        return [
            PortConnectionInfo(
                protocol=Protocol.TCP,
                identifier=port,
                direction=Direction.CONNECTING,
            )
            for host, port in zip(self.hosts, self.ports)
        ]
