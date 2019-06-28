"""Process worker pool module."""

import os
import re
import sys
import time
import signal
import subprocess
from schema import Or
import psutil
import tempfile

import testplan
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.process import kill_process
from testplan.common.utils.match import match_regexps_in_file
from testplan.runners.pools import tasks
from testplan.common.utils.timing import get_sleeper

from .base import Pool, PoolConfig, Worker, WorkerConfig
from .connection import ZMQClientProxy, ZMQServer


class ProcessWorkerConfig(WorkerConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.process.ProcessWorker` resource entity.

    :param start_timeout: Timeout duration for worker to start.
    :type start_timeout: ``int``
    :param transport: Transport class for pool/worker communication.
    :type transport: :py:class:`~testplan.runners.pools.connection.Client`

    Also inherits all :py:class:`~testplan.runners.pools.base.WorkerConfig`
    options.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption('start_timeout', default=120): int,
            ConfigOption('transport', default=ZMQClientProxy): object,
        }


class ProcessWorker(Worker):
    """
    Process worker resource that pulls tasks from the transport provided,
    executes them and sends back task results.
    """

    CONFIG = ProcessWorkerConfig

    def __init__(self, **options):
        super(ProcessWorker, self).__init__(**options)

    def _child_path(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(dirname, 'child.py')

    def _proc_cmd(self):
        """Command to start child process."""
        from testplan.common.utils.path import fix_home_prefix
        cmd = [sys.executable, fix_home_prefix(self._child_path()),
               '--index', self.cfg.index,
               '--address', self.transport.address,
               '--testplan', os.path.join(os.path.dirname(testplan.__file__),
                                          '..'),
               '--type', 'process_worker',
               '--log-level', TESTPLAN_LOGGER.getEffectiveLevel(),
               '--sys-path-file', self._write_syspath()]
        if os.environ.get(testplan.TESTPLAN_DEPENDENCIES_PATH):
            cmd.extend(
                ['--testplan-deps', fix_home_prefix(
                    os.environ[testplan.TESTPLAN_DEPENDENCIES_PATH])])
        return cmd

    def _write_syspath(self):
        """Write out our current sys.path to a file and return the filename."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('\n'.join(sys.path))
            self.logger.debug('Written sys.path to file: %s', f.name)
            return f.name

    def starting(self):
        """Start a child process worker."""
        # NOTE: Worker resource has no runpath.
        cmd = self._proc_cmd()
        self.logger.debug('{} executes cmd: {}'.format(self, cmd))

        with open(self.outfile, 'wb') as out:
            self._handler = subprocess.Popen(
                [str(a) for a in cmd],
                stdout=out, stderr=out, stdin=subprocess.PIPE
            )
        self.logger.debug('Started child process - output at %s', self.outfile)
        self._handler.stdin.write(bytes('y\n'.encode('utf-8')))

    def _wait_started(self, timeout=None):
        """TODO."""
        sleeper = get_sleeper(
            interval=(0.04, 0.5),
            timeout=self.cfg.start_timeout,
            raise_timeout_with_msg='Worker start timeout, logfile = {}'
                                   .format(self.outfile))
        while next(sleeper):
            if match_regexps_in_file(
                    self.outfile,
                    [re.compile('Starting child process worker on')])[0]:
                self.last_heartbeat = time.time()
                self.status.change(self.STATUS.STARTED)
                return

            if self._handler.poll() is not None:
                raise RuntimeError(
                    '{proc} process exited: {rc} (logfile = {log})'.format(
                        proc=self,
                        rc=self._handler.returncode,
                        log=self.outfile))

    @property
    def is_alive(self):
        if self._handler is None:
            self.logger.debug('No worker process started')
            return False

        # Check if the child process already terminated.
        if self._handler.poll() is not None:
            self.logger.critical('Worker process exited with code %d',
                                 self._handler.returncode)
            self._handler = None
            return False
        else:
            return True

    def stopping(self):
        """Stop child process worker."""
        if self._handler:
            kill_process(self._handler)
            self._handler.wait()
        self.status.change(self.STATUS.STOPPED)

    def aborting(self):
        """Process worker abort logic."""
        self._transport.disconnect()
        if hasattr(self, '_handler') and self._handler:
            kill_process(self._handler)
            self._handler.wait()
            self._handler = None


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
    CONN_MANAGER = ZMQServer

    def add(self, task, uid):
        """
        Before adding Tasks to a ProcessPool, check that the Task target does
        not come from __main__.
        """
        if isinstance(task, tasks.Task) and task.module == '__main__':
            raise ValueError('Cannot add Tasks from __main__ to ProcessPool')
        super(ProcessPool, self).add(task, uid)

