"""Connections module."""

import pickle
import warnings

import zmq

from .base import ConnectionManager


class TCPConnectionManager(ConnectionManager):
    """
    Manages pool-worker TCP communication.
    """

    def __init__(self):
        super(TCPConnectionManager, self).__init__()

        # Here, context is a factory class provided by ZMQ that creates
        # sockets. Context and other attributes below are set when starting
        # and cleaned up when stopping.
        self._context = None
        self._sock = None
        self._address = None

    def __del__(self):
        """
        Check that ZMQ sockets are properly closed when this manager is
        garbage-collected. If not we close them now as a fallback.
        """
        # Use getattr() with a default here - there is no guarantee that
        # __init__() has completed successfully when __del__() is called.
        if (getattr(self, '_sock', None) is not None) or (
                getattr(self, '_context', None) is not None):
            warnings.warn('Pool TCP connections were not closed.')
            self._close()

    def starting(self):
        """Create a ZMQ context and socket to handle TCP communication."""
        if self.parent is None:
            raise RuntimeError('Parent pool was not set - cannot start.')

        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REP)
        if self.parent.cfg.port == 0:
            port_selected = self._sock.bind_to_random_port(
                "tcp://{}".format(self.parent.cfg.host))
        else:
            self._sock.bind("tcp://{}:{}".format(self.parent.cfg.host,
                                                 self.parent.cfg.port))
            port_selected = self.parent.cfg.port
        self._address = '{}:{}'.format(self.parent.cfg.host, port_selected)
        super(TCPConnectionManager, self).starting()

    def stopping(self):
        """
        Terminate the ZMQ context and socket when stopping. We require that
        all workers are stopped before stopping the connection manager, so
        that we can safely remove references to connection sockets from the
        worker.
        """
        self._close()
        super(TCPConnectionManager, self).stopping()

    def aborting(self):
        """Terminate the ZMQ context and socket when aborting."""
        self._close()
        super(TCPConnectionManager, self).aborting()

    def register(self, worker):
        """Register a new worker."""
        super(TCPConnectionManager, self).register(worker)
        worker.transport.connection = self._sock
        worker.transport.address = self._address

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

    def _unregister_workers(self):
        """Remove references to TCP connections from workers."""
        for worker in self._workers:
            if worker.status.tag != worker.status.STOPPED:
                raise RuntimeError('Worker is not yet stopped - in state {}'
                                   .format(worker.status.tag))
            worker.transport.connection = None
            worker.transport.address = None
        super(TCPConnectionManager, self)._unregister_workers()

    def _close(self):
        """Closes TCP connections managed by this object.."""
        self.logger.debug('Closing TCP connections for %s', self.parent)
        self._sock.close()
        self._sock = None
        self._context.destroy()
        self._context = None
        self._address = None

