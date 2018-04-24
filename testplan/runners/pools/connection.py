"""Connections module."""

import pickle

import zmq

from .base import ConnectionManager


class TCPConnectionManager(ConnectionManager):
    """
    Manages pool-worker TCP communication.
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
