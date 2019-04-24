"""Connections module."""

import pickle
import warnings
import six
import abc
import zmq
import time
from six.moves import queue

from testplan.common import entity
from testplan.common.utils import logger


@six.add_metaclass(abc.ABCMeta)
class Client(logger.Loggable):
    """
    Workers are Client in Pool/Worker communication.
    Abstract base class for workers to communicate with its pool."""

    def __init__(self):
        super(Client, self).__init__()
        self.active = False

    @abc.abstractmethod
    def connect(self, server):
        """Connect client to server"""
        self.active = True

    @abc.abstractmethod
    def disconnect(self):
        """Disconnect client from server"""
        self.active = False

    @abc.abstractmethod
    def send(self, message):
        """
        Sends a message to server
        :param message: Message to be sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        pass

    @abc.abstractmethod
    def receive(self):
        """Receives response to the message sent"""
        pass

    def send_and_receive(self, message, expect=None):
        """
        Send and receive shortcut. Optionally assert that the response is
        of the type expected. I.e For a TaskSending message, an Ack is expected.

        :param message: Message sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        :param expect: Assert message received command is the expected.
        :type expect: ``NoneType`` or
            :py:class:`~testplan.runners.pools.communication.Message`
        :return: Message received.
        :rtype: ``object``
        """
        if not self.active:
            return None

        try:
            self.send(message)
        except Exception as exc:
            self.logger.exception('Exception on transport send: {}.'.format(exc))
            raise RuntimeError('On transport send - {}.'.format(exc))

        try:
            received = self.receive()
        except Exception as exc:
            self.logger.exception('Exception on transport receive: {}.'.format(exc))
            raise RuntimeError('On transport receive - {}.'.format(exc))

        if expect is not None:
            if received is None:
                raise RuntimeError('Received None when {} was expected.'.format(
                    expect))
            assert received.cmd == expect
        return received


class QueueClient(Client):
    """Queue based client implementation, for thread pool workers to communicate with its pool."""

    def __init__(self, recv_sleep=0.05):
        super(QueueClient, self).__init__()
        self._recv_sleep = recv_sleep
        self.requests = None
        self.responses = []     # single-producer(pool) single-consumer(worker) FIFO queue

    def connect(self, requests):
        """
        Connect to the request queue of Pool
        :param requests: request queue of pool that worker should write to.
        :type requests: Queue
        """
        self.requests = requests
        self.active = True

    def disconnect(self):
        """Disconnect worker from pool"""
        self.active = False
        self.requests = None

    def send(self, message):
        """
        Worker sends a message
        :param message: Message to be sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        if self.active:
            self.requests.put(message)

    def receive(self):
        """
        Worker receives response to the message sent, this method blocks.
        :return: Response to the message sent.
        :type: :py:class:`~testplan.runners.pools.communication.Message`
        """
        while self.active:
            try:
                return self.responses.pop()
            except IndexError:
                time.sleep(self._recv_sleep)

    def respond(self, message):
        """
        Used by :py:class:`~testplan.runners.pools.base.Pool` to respond to
        worker request.

        :param message: Respond message.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        if self.active:
            self.responses.append(message)


class ZMQClient(Client):
    """
    ZMQ based client implementation for process worker to communicate with its pool.
    :param address: Pool server address to connect to.
    :type address: ``float``
    :param recv_sleep: Sleep duration in msg receive loop.
    :type recv_sleep: ``float``
    """

    def __init__(self, address, recv_sleep=0.05, recv_timeout=5):
        super(ZMQClient, self).__init__()
        self._address = address
        self._recv_sleep = recv_sleep
        self._recv_timeout = recv_timeout
        self._context = None
        self._sock = None

        self.connect()  # auto connect

    def connect(self):
        """Connect to a ZMQ Server"""
        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REQ)
        self._sock.connect("tcp://{}".format(self._address))
        self.active = True

    def disconnect(self):
        """Disconnect from Server"""
        self.active = True
        self._sock.close()
        self._sock = None
        self._context.destroy()
        self._context = None

    def send(self, message):
        """
        Worker sends a message.

        :param message: Message to be sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        if self.active:
            self._sock.send(pickle.dumps(message))

    def receive(self):
        """
        Worker tries to receive the response to the message sent until timeout.

        :return: Response to the message sent.
        :type: :py:class:`~testplan.runners.pools.communication.Message`
        """
        start_time = time.time()

        while self.active:
            try:
                received = self._sock.recv(flags=zmq.NOBLOCK)
                try:
                    loaded = pickle.loads(received)
                except Exception as exc:
                    print('Deserialization error. - {}'.format(exc))
                    raise
                else:
                    return loaded
            except zmq.Again:
                if time.time() - start_time > self._recv_timeout:
                    print('Transport receive timeout {}s reached!'.format(
                        self._recv_timeout))
                    return None
                time.sleep(self._recv_sleep)
        return None


class ZMQClientProxy(object):
    """
    Representative of a process worker's transport in local worker object.
    """

    def __init__(self):
        self.connection = None
        self.address = None

    def respond(self, message):
        """
        Used by :py:class:`~testplan.runners.pools.base.Pool` to respond to
        worker request.

        :param message: Respond message.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        self.connection.send(pickle.dumps(message))


@six.add_metaclass(abc.ABCMeta)
class Server(entity.Resource):
    """
    Abstract base class for pools to communicate to its workers.
    """

    def __init__(self):
        super(Server, self).__init__()
        self._workers = []

    @property
    def workers(self):
        return self._workers

    def starting(self):
        """Server starting logic."""
        self.status.change(self.status.STARTED)

    def stopping(self):
        """Server stopping logic."""

        self._unregister_workers()
        self.status.change(self.status.STOPPED)

    def aborting(self):
        """Abort policy - no abort actions are required in the base class."""
        pass

    @abc.abstractmethod
    def register(self, worker):
        """
        Register a new worker. Workers should be registered after the
        connection manager is started and will be automatically unregistered
        when it is stopped.
        """
        if self.status.tag != self.status.STARTED:
            raise RuntimeError(
                'Can only register workers when started. Current state is {}'
                .format(self.status.tag))

        if worker in self._workers:
            raise RuntimeError('Worker {} already in ConnectionManager'.format(worker))
        self._workers.append(worker)

    @abc.abstractmethod
    def _unregister_workers(self):
        """Remove workers from this connection manager."""
        self._workers = []

    @abc.abstractmethod
    def accept(self):
        """
        Accepts a new message from worker. This method should not block - if
        no message is queued for receiving it should return None.

        :return: Message received from worker transport, or None.
        :rtype: ``NoneType`` or
            :py:class:`~testplan.runners.pools.communication.Message`
        """
        pass


class QueueServer(Server):
    """Queue based server implementation, for thread pool to get requests from workers."""

    def __init__(self):
        super(QueueServer, self).__init__()
        self.requests = queue.Queue()     # multi-producer(workers) single-consumer(pool) FIFO queue

    def register(self, worker):
        super(QueueServer, self).register(worker)
        worker.transport.connect(self.requests)

    def _unregister_workers(self):
        for worker in self._workers:
            worker.transport.disconnect()
        super(QueueServer, self)._unregister_workers()

    def accept(self):
        """
        Accepts the next request in the request queue.

        :return: Message received from worker transport, or None.
        :rtype: ``NoneType`` or
            :py:class:`~testplan.runners.pools.communication.Message`
        """
        try:
            return self.requests.get()
        except queue.Empty:
            return None


class ZMQServer(Server):
    """
    ZMQ based server implementation, for process/remote/treadmill pool to get request from workers.
    """

    def __init__(self):
        super(ZMQServer, self).__init__()

        # Here, context is a factory class provided by ZMQ that creates
        # sockets. Context and other attributes below are set when starting
        # and cleaned up when stopping.
        self._zmq_context = None
        self._sock = None
        self._address = None

    def starting(self):
        """Create a ZMQ context and socket to handle TCP communication."""
        if self.parent is None:
            raise RuntimeError('Parent pool was not set - cannot start.')

        self._zmq_context = zmq.Context()
        self._sock = self._zmq_context.socket(zmq.REP)
        if self.parent.cfg.port == 0:
            port_selected = self._sock.bind_to_random_port(
                "tcp://{}".format(self.parent.cfg.host))
        else:
            self._sock.bind("tcp://{}:{}".format(self.parent.cfg.host,
                                                 self.parent.cfg.port))
            port_selected = self.parent.cfg.port
        self._address = '{}:{}'.format(self.parent.cfg.host, port_selected)
        super(ZMQServer, self).starting()

    def _close(self):
        """Closes TCP connections managed by this object.."""
        self.logger.debug('Closing TCP connections for %s', self.parent)
        self._sock.close()
        self._sock = None
        self._zmq_context.destroy()
        self._zmq_context = None
        self._address = None

    def stopping(self):
        """
        Terminate the ZMQ context and socket when stopping. We require that
        all workers are stopped before stopping the connection manager, so
        that we can safely remove references to connection sockets from the
        worker.
        """
        self._close()
        super(ZMQServer, self).stopping()

    def aborting(self):
        """Terminate the ZMQ context and socket when aborting."""
        self._close()
        super(ZMQServer, self).aborting()

    def register(self, worker):
        """Register a new worker."""
        super(ZMQServer, self).register(worker)
        worker.transport.connection = self._sock
        worker.transport.address = self._address

    def _unregister_workers(self):
        """Remove references to TCP connections from workers."""
        for worker in self._workers:
            if worker.status.tag != worker.status.STOPPED:
                raise RuntimeError('Worker is not yet stopped - in state {}'
                                   .format(worker.status.tag))
            worker.transport.connection = None
            worker.transport.address = None
        super(ZMQServer, self)._unregister_workers()

    def accept(self):
        """
        Accepts a new message from worker. Doesn't block if no message is
        queued for receiving.

        :return: Message received from worker transport, or None.
        :rtype: ``NoneType`` or
            :py:class:`~testplan.runners.pools.communication.Message`
        """
        try:
            return pickle.loads(self._sock.recv(flags=zmq.NOBLOCK))
        except zmq.Again:
            return None

    def __del__(self):
        """
        Check that ZMQ sockets are properly closed when this manager is
        garbage-collected. If not we close them now as a fallback.
        """
        # Use getattr() with a default here - there is no guarantee that
        # __init__() has completed successfully when __del__() is called.
        if (getattr(self, '_sock', None) is not None) or (
                getattr(self, '_zmq_context', None) is not None):
            warnings.warn('Pool TCP connections were not closed.')
            self._close()