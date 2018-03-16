"""Process worker pool module."""

import os
import sys
import pickle
import signal
import subprocess

import zmq

from schema import Or, And, Use

from .base import Pool, PoolConfig, Worker, WorkerConfig, ConnectionManager

import testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.process import kill_process


class ProcessTransport(object):
    """
    Transport layer for communication between a pool and a process worker.
    Worker send serializable messages, pool receives and send back responses.

    :param recv_sleep: Sleep duration in msg receive loop.
    :type recv_sleep: ``float``
    """

    def __init__(self, recv_sleep=0.05):
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


class ProcessWorkerConfig(WorkerConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.process.ProcessWorker` resource entity.

    :param transport: Transport communication class definition.
    :type transport: :py:class:`~testplan.runners.pools.process.ProcessTransport`

    Also inherits all :py:class:`~testplan.runners.pools.base.WorkerConfig`
    options.
    """

    def configuration_schema(self):
        """
        Schema for options validation and assignment of default values.
        """
        overrides = {
            ConfigOption('transport', default=ProcessTransport): object,
        }
        return self.inherit_schema(overrides, super(ProcessWorkerConfig, self))


class ProcessWorker(Worker):
    """
    Process worker resource that pulls tasks from the transport provided,
    executes them and sends back task results.
    """

    CONFIG = ProcessWorkerConfig

    def starting(self):
        """Start a child process worker."""
        # NOTE: Worker resource has no runpath.
        # TODO env fallback on resource failing to start
        dirname = os.path.dirname(os.path.abspath(__file__))

        cmd = [sys.executable, os.path.join(dirname, 'child.py'),
               '--index', self.cfg.index,
               '--address', self.transport.address,
               '--testplan', os.path.join(os.path.dirname(testplan.__file__),
                                          '..'),
               '--type', 'process_worker',
               '--log-level', TESTPLAN_LOGGER.getEffectiveLevel()]

        self.logger.debug('Starting process child with cmd: {}'.format(cmd))
        with open(self.outfile, 'wb') as out:
            with open(self.errfile, 'wb') as err:
                self._handler = subprocess.Popen(
                    [str(a) for a in cmd],
                    stdout=out, stderr=err,
                    env={name: os.environ[name] for name in os.environ}
                )

    def stopping(self):
        """Stop child process worker."""
        self._transport.active = False
        if self._handler:
            kill_process(self._handler)
            self._handler.wait()
        self.status.change(self.STATUS.STOPPED)

    def aborting(self):
        """Process worker abort logic."""
        self._transport.active = False
        if self._handler:
            kill_process(self._handler)
            self._handler.wait()


class ProcessPoolConfig(PoolConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.process.ProcessPool` executor
    resource entity.

    :param abort_signals: Signals to trigger abort logic. Default: INT, TERM.
    :type abort_signals: ``list`` of ``int``
    :param worker_type: Type of worker to be initialized.
    :type worker_type: :py:class:`~testplan.runners.pools.process.ProcessWorker`
    :param host: Host that pool binds and listens for requests.
    :type host: ``str``
    :param port: Port that pool binds. Default: 0 (random)
    :type port: ``int``
    :param worker_heartbeat: Worker heartbeat period.
    :type worker_heartbeat: ``int`` or ``float`` or ``NoneType``

    Also inherits all :py:class:`~testplan.runners.pools.base.PoolConfig`
    options.
    """

    def configuration_schema(self):
        """
        Schema for options validation and assignment of default values.
        """
        overrides = {
            ConfigOption('abort_signals', default=[signal.SIGINT,
                                                   signal.SIGTERM]): [int],
            ConfigOption('worker_type', default=ProcessWorker): object,
            ConfigOption('host', default='127.0.0.1'): str,
            ConfigOption('port', default=0): int,
            ConfigOption('worker_heartbeat', default=5): Or(int, float, None)
        }
        return self.inherit_schema(overrides, super(ProcessPoolConfig, self))


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


class ProcessPool(Pool):
    """
    Pool task executor object that initializes process workers and dispatches
    tasks.
    """

    CONFIG = ProcessPoolConfig
    CONN_MANAGER = TCPConnectionManager
