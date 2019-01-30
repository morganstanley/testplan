"""Connections module."""

import pickle
import logging
import zmq
import time

from .base import ConnectionManager


class ZMQConnectionServer(ConnectionManager):
    """
    Manages pool-worker communication via ZMQ, this is the server side.
    """

    def __init__(self, cfg):
        """TODO."""
        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REP)
        if cfg.port == 0:
            port_selected = self._sock.bind_to_random_port(
                "tcp://{}".format(cfg.host))
        else:
            self._sock.bind("tcp://{}:{}".format(cfg.host, cfg.port))
            port_selected = cfg.port
        self._address = '{}:{}'.format(cfg.host, port_selected)

    def register(self, worker):
        """Register a new worker."""
        worker.transport.connection = self._sock
        worker.transport.address = self._address

    def accept(self):
        """
        Accepts a new message from worker.

        :return: Message received from worker transport.
        :rtype: ``NoneType`` or
            :py:class:`~testplan.runners.pools.communication.Message`
        """
        try:
            return pickle.loads(self._sock.recv(flags=zmq.NOBLOCK))
        except zmq.Again:
            return None

    def close(self):
        """Closes TCP connections."""
        self._sock.close()

class ZMQConnectionClient(object):
    """
    Transport layer for communication between a pool and child process worker.
    Worker send serializable messages, pool receives and send back responses.

    :param address: Pool address to connect to.
    :type address: ``float``
    :param recv_sleep: Sleep duration in msg receive loop.
    :type recv_sleep: ``float``
    """

    def __init__(self, address, recv_sleep=0.05, recv_timeout=5):
        import zmq
        self._zmq = zmq
        self._recv_sleep = recv_sleep
        self._recv_timeout = recv_timeout
        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REQ)
        self._sock.connect("tcp://{}".format(address))
        self.active = True
        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self, message):
        """
        Worker sends a message.

        :param message: Message to be sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        self._sock.send(pickle.dumps(message))

    def receive(self):
        """
        Worker receives the response to the message sent.

        :return: Response to the message sent.
        :type: :py:class:`~testplan.runners.pools.communication.Message`
        """
        start_time = time.time()
        while self.active:
            try:
                received = self._sock.recv(flags=self._zmq.NOBLOCK)
                try:
                    loaded = pickle.loads(received)
                except Exception as exc:
                    print('Deserialization error. - {}'.format(exc))
                    raise
                else:
                    return loaded
            except self._zmq.Again:
                if time.time() - start_time > self._recv_timeout:
                    print('Transport receive timeout {}s reached!'.format(
                        self._recv_timeout))
                    return None
                time.sleep(self._recv_sleep)
        return None
