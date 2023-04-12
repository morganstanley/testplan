"""Connections module."""

import abc
import queue
import time
import warnings
from typing import List, Optional, Tuple, Union

import zmq

from testplan.common import entity
from testplan.common.serialization import deserialize, serialize
from testplan.common.utils import logger
from testplan.runners.pools.communication import Message


class Client(logger.Loggable, metaclass=abc.ABCMeta):
    """
    Workers are Client in Pool/Worker communication.
    Abstract base class for workers to communicate with its pool."""

    def __init__(self) -> None:
        super(Client, self).__init__()
        self.active = False

    @abc.abstractmethod
    def connect(self, server) -> None:
        """Connect client to server"""
        self.active = True

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect client from server"""
        self.active = False

    @abc.abstractmethod
    def send(self, message: Message) -> None:
        """
        Sends a message to server.

        :param message: Message to be sent.
        """
        pass

    @abc.abstractmethod
    def receive(self) -> Optional[Message]:
        """Receives response to the message sent"""
        pass

    def send_and_receive(
        self,
        message: Message,
        expect: Union[None, Tuple, List, Message] = None,
    ) -> Optional[Message]:
        """
        Send and receive shortcut. Optionally assert that the response is
        of the type expected. I.e For a TaskSending message, an Ack is
        expected.

        :param message: Message sent.
        :param expect: Expected command of message received.
        :return: Message received.
        """
        if not self.active:
            return None

        try:
            self.send(message)
        except Exception as exc:
            self.logger.exception("Exception on transport send: %s.", exc)
            raise RuntimeError(f"On transport send - {exc}.")

        try:
            received = self.receive()
        except Exception as exc:
            self.logger.exception("Exception on transport receive: %s.", exc)
            raise RuntimeError(f"On transport receive - {exc}.")

        if expect is not None:
            if received is None:
                raise RuntimeError(
                    f"Received None when {expect} was expected."
                )
            if isinstance(expect, (tuple, list)):
                assert received.cmd in expect
            else:
                assert received.cmd == expect
        return received


class QueueClient(Client):
    """
    Queue based client implementation, for thread pool workers to
    communicate with its pool.
    """

    def __init__(self, recv_sleep: float = 0.05) -> None:
        super(QueueClient, self).__init__()
        self._recv_sleep = recv_sleep
        self.requests: Optional[queue.Queue] = None

        # single-producer(pool) single-consumer(worker) FIFO queue
        self.responses = []

    def connect(self, requests: queue.Queue) -> None:
        """
        Connect to the request queue of Pool
        :param requests: request queue of pool that worker should write to.
        :type requests: Queue
        """
        self.requests = requests
        self.active = True

    def disconnect(self) -> None:
        """Disconnect worker from pool"""
        self.active = False
        self.requests = None

    def send(self, message: Message) -> None:
        """
        Worker sends a message

        :param message: Message to be sent.
        """
        if self.active:
            self.requests.put(message)

    def receive(self) -> Message:
        """
        Worker receives response to the message sent, this method blocks.

        :return: Response to the message sent.
        """
        while self.active:
            try:
                return self.responses.pop()
            except IndexError:
                time.sleep(self._recv_sleep)

    def respond(self, message: Message) -> None:
        """
        Used by :py:class:`~testplan.runners.pools.base.Pool` to respond to
        worker request.

        :param message: Respond message.
        """
        if self.active:
            self.responses.append(message)
        else:
            raise RuntimeError("Responding to inactive worker")


class ZMQClient(Client):
    """
    ZMQ based client implementation for process worker to communicate
    with its pool.

    :param address: Pool server address to connect to.
    :param recv_sleep: Sleep duration in msg receive loop.
    """

    def __init__(
        self,
        address: str,
        recv_sleep: float = 0.05,
        recv_timeout: float = 5,
    ) -> None:
        super(ZMQClient, self).__init__()
        self._address = address
        self._recv_sleep = recv_sleep
        self._recv_timeout = recv_timeout
        self._context = None
        self._sock = None

        self.connect()  # auto connect

    def connect(self) -> None:
        """Connect to a ZMQ Server"""
        # pylint: disable=abstract-class-instantiated
        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REQ)
        self._sock.connect("tcp://{}".format(self._address))
        self.active = True

    def disconnect(self) -> None:
        """Disconnect from Server"""
        self.active = False
        self._sock.close()
        self._sock = None
        self._context.destroy()
        self._context = None
        self._address = None

    def send(self, message: Message) -> None:
        """
        Worker sends a message.

        :param message: Message to be sent.
        """
        if self.active:
            self._sock.send(serialize(message))

    def receive(self) -> Optional[Message]:
        """
        Worker tries to receive the response to the message sent until timeout.

        :return: Response to the message sent.
        """
        start_time = time.time()

        while self.active:
            try:
                received = self._sock.recv(flags=zmq.NOBLOCK)
                try:
                    loaded = deserialize(received)
                except Exception as exc:
                    print(f"Deserialization error. - {exc}")
                    raise
                else:
                    return loaded
            except zmq.Again:
                if time.time() - start_time > self._recv_timeout:
                    print(
                        f"Transport receive timeout {self._recv_timeout}s"
                        f" reached!"
                    )
                    return None
                time.sleep(self._recv_sleep)
        return None


class ZMQClientProxy:
    """
    Representative of a process worker's transport in local worker object.
    """

    def __init__(self) -> None:
        self.active = False
        self.connection = None
        self.address = None

    def connect(self, server) -> None:
        self.connection = server.sock
        self.address = server.address
        self.active = True

    def disconnect(self) -> None:
        self.active = False
        self.connection = None
        self.address = None

    def respond(self, message: Message) -> None:
        """
        Used by :py:class:`~testplan.runners.pools.base.Pool` to respond to
        worker request.

        :param message: Respond message.
        """
        if self.active:
            self.connection.send(serialize(message))
        else:
            raise RuntimeError("Responding to inactive worker")


class Server(entity.Resource, metaclass=abc.ABCMeta):
    """
    Abstract base class for pools to communicate to its workers.
    """

    def __init__(self) -> None:
        super(Server, self).__init__()

    def starting(self) -> None:
        """Server starting logic."""
        self.status.change(self.status.STARTED)  # Start is async

    def stopping(self) -> None:
        """Server stopping logic."""
        self.status.change(self.status.STOPPED)  # Stop is async

    def aborting(self) -> None:
        """Abort policy - no abort actions are required in the base class."""
        pass

    @abc.abstractmethod
    def register(self, worker: "Worker") -> None:
        """
        Register a new worker. Workers should be registered after the
        connection manager is started and will be automatically unregistered
        when it is stopped.
        """
        if self.status != self.status.STARTED:
            raise RuntimeError(
                "Can only register workers when started."
                f" Current state is {self.status.tag}."
            )

    @abc.abstractmethod
    def accept(self) -> Optional[Message]:
        """
        Accepts a new message from worker. This method should not block - if
        no message is queued for receiving it should return None.

        :return: Message received from worker transport, or None.
        """
        pass


class QueueServer(Server):
    """
    Queue based server implementation, for thread pool to get requests
    from workers.
    """

    def __init__(self) -> None:
        super(QueueServer, self).__init__()

        # multi-producer(workers) single-consumer(pool) FIFO queue
        self.requests = None

    def starting(self) -> None:
        self.requests = queue.Queue()
        super(QueueServer, self).starting()

    def register(self, worker) -> None:
        super(QueueServer, self).register(worker)
        worker.transport.connect(self.requests)

    def accept(self) -> Optional[Message]:
        """
        Accepts the next request in the request queue.

        :return: Message received from worker transport, or None.
        """
        try:
            return self.requests.get_nowait()
        except queue.Empty:
            return None


class ZMQServer(Server):
    """
    ZMQ based server implementation, for process/remote/treadmill pool
    to get request from workers.
    """

    def __init__(self) -> None:
        super(ZMQServer, self).__init__()

        # Here, context is a factory class provided by ZMQ that creates
        # sockets. Context and other attributes below are set when starting
        # and cleaned up when stopping.
        self._zmq_context = None
        self._sock = None
        self._address = None

    @property
    def sock(self):
        return self._sock

    @property
    def address(self):
        return self._address

    def starting(self):
        """Create a ZMQ context and socket to handle TCP communication."""
        if self.parent is None:
            raise RuntimeError("Parent pool was not set - cannot start.")

        # pylint: disable=abstract-class-instantiated
        self._zmq_context = zmq.Context()
        self._sock = self._zmq_context.socket(zmq.REP)
        if self.parent.cfg.port == 0:
            port_selected = self._sock.bind_to_random_port(
                "tcp://{}".format(self.parent.cfg.host)
            )
        else:
            self._sock.bind(
                "tcp://{}:{}".format(
                    self.parent.cfg.host, self.parent.cfg.port
                )
            )
            port_selected = self.parent.cfg.port
        self._address = "{}:{}".format(self.parent.cfg.host, port_selected)
        super(ZMQServer, self).starting()

    def _close(self) -> None:
        """Closes TCP connections managed by this object.."""
        self.logger.debug("Closing TCP connections for %s", self.parent)
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        if self._zmq_context is not None:
            self._zmq_context.destroy()
            self._zmq_context = None
        self._address = None

    def stopping(self) -> None:
        """
        Terminate the ZMQ context and socket when stopping. We require that
        all workers are stopped before stopping the connection manager, so
        that we can safely remove references to connection sockets from the
        worker.
        """
        self._close()
        super(ZMQServer, self).stopping()

    def aborting(self) -> None:
        """Terminate the ZMQ context and socket when aborting."""
        if self._sock is not None:
            self._close()
        super(ZMQServer, self).aborting()

    def register(self, worker) -> None:
        """Register a new worker."""
        super(ZMQServer, self).register(worker)
        worker.transport.connect(self)

    def accept(self) -> Optional[Message]:
        """
        Accepts a new message from worker. Doesn't block if no message is
        queued for receiving.

        :return: Message received from worker transport, or None.
        """
        try:
            return deserialize(self._sock.recv(flags=zmq.NOBLOCK))
        except zmq.Again:
            return None

    def __del__(self) -> None:
        """
        Check that ZMQ sockets are properly closed when this manager is
        garbage-collected. If not we close them now as a fallback.
        """
        # Use getattr() with a default here - there is no guarantee that
        # __init__() has completed successfully when __del__() is called.
        if (getattr(self, "_sock", None) is not None) or (
            getattr(self, "_zmq_context", None) is not None
        ):
            warnings.warn("Pool TCP connections were not closed.")
            self._close()
