"""Process worker pool module."""

import os
import re
import sys
import time
import pickle
import signal
import subprocess
from schema import Or, And, Use

import testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.process import kill_process
from testplan.common.utils.match import match_regexps_in_file

from .base import Pool, PoolConfig, Worker, WorkerConfig
from .connection import TCPConnectionManager


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

    :param start_timeout: Timeout duration for worker to start.
    :type start_timeout: ``int``
    :param transport: Transport communication class definition.
    :type transport: :py:class:`~testplan.runners.pools.process.ProcessTransport`

    Also inherits all :py:class:`~testplan.runners.pools.base.WorkerConfig`
    options.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption('start_timeout', default=30): int,
            ConfigOption('transport', default=ProcessTransport): object,
        }


class ProcessWorker(Worker):
    """
    Process worker resource that pulls tasks from the transport provided,
    executes them and sends back task results.
    """

    CONFIG = ProcessWorkerConfig

    def _proc_cmd(self):
        """Command to start child process."""
        dirname = os.path.dirname(os.path.abspath(__file__))
        cmd = [sys.executable, os.path.join(dirname, 'child.py'),
               '--index', self.cfg.index,
               '--address', self.transport.address,
               '--testplan', os.path.join(os.path.dirname(testplan.__file__),
                                          '..'),
               '--type', 'process_worker',
               '--log-level', TESTPLAN_LOGGER.getEffectiveLevel()]
        if os.environ.get(testplan.TESTPLAN_DEPENDENCIES_PATH):
            cmd.extend(
                ['--testplan-deps',
                 os.environ[testplan.TESTPLAN_DEPENDENCIES_PATH]])
        return cmd

    def starting(self):
        """Start a child process worker."""
        # NOTE: Worker resource has no runpath.
        cmd = self._proc_cmd()
        self.logger.debug('{} executes cmd: {}'.format(self, cmd))

        with open(self.outfile, 'wb') as out:
            with open(self.errfile, 'wb') as err:
                self._handler = subprocess.Popen(
                    [str(a) for a in cmd],
                    stdout=out, stderr=err, stdin=subprocess.PIPE
                )

        self._handler.stdin.write(bytes('y\n'.encode('utf-8')))

    def _wait_started(self, timeout=None):
        """TODO."""
        st_time = time.time()
        sleep_interval = 0.04
        while time.time() - st_time < self.cfg.start_timeout:
            time.sleep(min(sleep_interval, 0.5))
            if match_regexps_in_file(
                  self.outfile,
                  [re.compile('Starting child process worker on')])[0] is True:
                self.status.change(self.STATUS.STARTED)
                return
            sleep_interval *= 2
        if self._handler.poll() is not None:
            raise RuntimeError('{} process exited: {}'.format(
                self, self._handler.poll()))
        raise RuntimeError(
            'Could not match starting pattern in {}'.format(self.outfile))

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

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption('abort_signals', default=[signal.SIGINT,
                                                   signal.SIGTERM]): [int],
            ConfigOption('worker_type', default=ProcessWorker): object,
            ConfigOption('host', default='127.0.0.1'): str,
            ConfigOption('port', default=0): int,
            ConfigOption('worker_heartbeat', default=5): Or(int, float, None)
        }


class ProcessPool(Pool):
    """
    Pool task executor object that initializes process workers and dispatches
    tasks.
    """

    CONFIG = ProcessPoolConfig
    CONN_MANAGER = TCPConnectionManager
