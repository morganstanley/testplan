"""Remote worker pool module."""

import os
import sys
import signal
import socket
import getpass
import platform
import subprocess

from schema import Or

import testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.path import module_abspath, pwd
from testplan.common.utils.remote import (
    ssh_cmd, copy_cmd, remote_filepath_exists)

from .base import Pool, PoolConfig
from .process import ProcessWorker, ProcessWorkerConfig
from .connection import TCPConnectionManager


class RemoteWorkerConfig(ProcessWorkerConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.remote.RemoteWorker` resource entity.

    :param workers: Number of remote workers of remote pool of child worker.
    :type workers: ``int``
    :param pool_type: Remote pool type that child worker will use.
    :type pool_type: ``str``

    Also inherits all :py:class:`~testplan.runners.pools.process.ProcessWorkerConfig`
    options.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            'workers': int,
            'pool_type': str,
        }


class RemoteWorker(ProcessWorker):
    """
    Remote worker resource that pulls tasks from the transport provided,
    executes them in a local pool of workers and sends back task results.
    """

    CONFIG = RemoteWorkerConfig

    def __init__(self, **options):
        super(RemoteWorker, self).__init__(**options)
        self._remote_testplan_path = None
        self._user = getpass.getuser()
        self._workspace_paths = {}
        self._child_paths = {}
        self._workspace_transferred = True

    def _execute_cmd(self, cmd):
        """Execute a subprocess command."""
        self.logger.debug('Executing command: {}'.format(cmd))
        handler = subprocess.Popen(
            [str(a) for a in cmd],
            stdout=sys.stdout, stderr=sys.stderr, stdin=subprocess.PIPE)
        handler.stdin.write(bytes('y\n'.encode('utf-8')))
        handler.wait()
        return handler.returncode

    def _create_remote_dirs(self):
        """Create mandatory directories in remote host."""
        testplan_path_dirs = ['', 'var', 'tmp', getpass.getuser(), 'testplan']
        self._remote_testplan_path = '/'.join(
            testplan_path_dirs + ['remote_workspaces',
                                  self.cfg.parent.parent.name])
        cmd = self.cfg.remote_mkdir + [self._remote_testplan_path]
        self._execute_cmd(
            self.cfg.ssh_cmd(self.cfg.index, ' '.join([str(a) for a in cmd])))

    def _copy_child_script(self):
        """Copy the remote worker executable file."""
        self._child_paths['remote'] = '{}/child.py'.format(
            self._remote_testplan_path)
        self._transfer_data(
            source=self._child_paths['local'],
            target='{}@{}:{}'.format(
                self._user, self.cfg.index, self._child_paths['remote']))

    def _copy_dependencies_module(self):
        """Copy mandatory dependencies need to be imported before testplan."""
        path = os.environ.get('TESTPLAN_DEPENDENCIES_PATH')
        if path is None:
            return
        local_path = '{}/dependencies.py'.format(path)
        remote_path = '{}/dependencies.py'.format(self._remote_testplan_path)
        self._transfer_data(
            source=local_path,
            target='{}@{}:{}'.format(
                self._user, self.cfg.index, remote_path))

    def _copy_workspace(self):
        """Copy the local workspace to remote host."""
        if self.cfg.remote_workspace:
            self._workspace_paths['remote'] = self.cfg.remote_workspace
            return
        self._transfer_data(
            source=self._workspace_paths['local'],
            target='{}@{}:{}'.format(
                self._user, self.cfg.index, self._remote_testplan_path))
        self._workspace_paths['remote'] = '{}/{}'.format(
            self._remote_testplan_path,
            self._workspace_paths['local'].split(os.sep)[-1])

    def _transfer_data(self, source, target):
        cmd = self.cfg.copy_cmd(source, target)
        self._execute_cmd(cmd)

    def _prepare_remote(self):
        """Transfer local data to remote host."""
        import testplan.runners.pools.child as child
        self._child_paths['local'] = module_abspath(child, self._user)
        self._working_dirs = {'local': pwd()}
        self._workspace_paths['local'] = self.cfg.workspace

        if self.cfg.copy_workspace_check:
            cmd = self.cfg.copy_workspace_check(
                self.cfg.ssh_cmd,
                self.cfg.index,
                self._workspace_paths['local'])
            self._workspace_transferred = self._execute_cmd(cmd) != 0

        if self._workspace_transferred is True:
            self._create_remote_dirs()
            self._copy_child_script()
            self._copy_dependencies_module()
            self._copy_workspace()

            self._working_dirs = {
                'local': pwd(),
                'remote': '{}{}'.format(
                    self._workspace_paths['remote'],
                    '/'.join(pwd().split(os.sep)).replace(
                        '/'.join(self._workspace_paths['local'].split(os.sep)),
                        ''))}
        else:
            self._child_paths['remote'] = self._child_paths['local']
            self._working_dirs['remote'] = self._working_dirs['local']
            self._workspace_paths['remote'] = self._workspace_paths['local']

    def _add_testplan_import_path(self, cmd, flag=None):
        if self.cfg.testplan_path:
            if flag is not None:
                cmd.append(flag)
            cmd.append(self.cfg.testplan_path)
            return

        import testplan
        testplan_path = os.path.abspath(
            os.path.join(
                os.path.dirname(module_abspath(testplan)),
                '..'))
        # Import testplan from outside the local workspace
        if not testplan_path.startswith(self._workspace_paths['local']):
            return
        common_prefix = os.path.commonprefix([testplan_path,
                                              self._workspace_paths['local']])
        if flag is not None:
            cmd.append(flag)
        cmd.append('{}/{}'.format(
            self._workspace_paths['remote'],
            '/'.join(os.path.relpath(
                testplan_path, common_prefix).split(os.sep))))

    def _add_testplan_deps_import_path(self, cmd, flag=None):
        if self._workspace_transferred is True:
            return
        if os.environ.get(testplan.TESTPLAN_DEPENDENCIES_PATH):
            if flag is not None:
                cmd.append(flag)
            cmd.append(os.environ[testplan.TESTPLAN_DEPENDENCIES_PATH])

    def _proc_cmd(self):
        """Command to start child process."""
        if platform.system() == 'Windows':
            if platform.python_version().startswith('3'):
                python_binary = os.environ['PYTHON3_REMOTE_BINARY']
            else:
                python_binary = os.environ['PYTHON2_REMOTE_BINARY']
        else:
            python_binary = sys.executable
        cmd = [python_binary, '-uB',
               self._child_paths['remote'],
               '--index', str(self.cfg.index),
               '--address', self.transport.address,
               '--type', 'remote_worker',
               '--log-level', str(TESTPLAN_LOGGER.getEffectiveLevel()),
               '--wd', self._working_dirs['remote'],
               '--remote-pool-type', self.cfg.pool_type,
               '--remote-pool-size', str(self.cfg.workers)]
        self._add_testplan_import_path(cmd, flag='--testplan')
        self._add_testplan_deps_import_path(cmd, flag='--testplan-deps')
        return self.cfg.ssh_cmd(self.cfg.index, ' '.join(cmd))

    def starting(self):
        """Start a child remote worker."""
        self._prepare_remote()
        super(RemoteWorker, self).starting()


class RemotePoolConfig(PoolConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.remote.RemotePool` executor
    resource entity.

    :param hosts: Map of host(ip): number of their local workers.
      i.e {'hostname1': 2, '10.147.XX.XX': 4}
    :type hosts: ``dict`` of ``str``:``int``
    :param abort_signals: Signals to trigger abort logic. Default: INT, TERM.
    :type abort_signals: ``list`` of ``int``
    :param worker_type: Type of worker to be initialized.
    :type worker_type: :py:class:`~testplan.runners.pools.remote.RemoteWorker`
    :param pool_type: Local pool that will be initialized in remote workers.
      i.e ``thread``, ``process``.
    :type pool_type: ``str``
    :param host: Host that pool binds and listens for requests. Defaults to
      local hostname.
    :type host: ``str``
    :param port: Port that pool binds. Default: 0 (random)
    :type port: ``int``
    :param copy_cmd: Creates the remote copy command.
    :type copy_cmd: ``callable``
    :param ssh_cmd: Creates the ssh command.
    :type ssh_cmd: ``callable``
    :param workspace: Current project workspace to be transferred.
    :type workspace: ``str``
    :param remote_workspace: Use a workspace that already exists in remote host.
    :type remote_workspace: ``str``
    :param copy_workspace_check: Check to indicate whether to copy workspace.
    :type copy_workspace_check: ``callable``
    :param remote_mkdir: Command to make directories in remote worker.
    :type remote_mkdir: ``list`` of ``str``
    :param testplan_path: Path to import testplan from.
    :type testplan_path: ``str``
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
        hostname = socket.gethostbyname(socket.gethostname())
        return {
            'hosts': dict,
            ConfigOption('abort_signals', default=[signal.SIGINT,
                                                   signal.SIGTERM]): [int],
            ConfigOption('worker_type', default=RemoteWorker): object,
            ConfigOption('pool_type', default='thread'): str,
            ConfigOption('host', default=hostname): str,
            ConfigOption('port', default=0): int,
            ConfigOption('copy_cmd', default=copy_cmd):
                lambda x: callable(x),
            ConfigOption('ssh_cmd', default=ssh_cmd):
                lambda x: callable(x),
            ConfigOption('workspace', default=pwd()): str,
            ConfigOption('remote_workspace', default=None): Or(str, None),
            ConfigOption('copy_workspace_check',
                         default=remote_filepath_exists):
                Or(lambda x: callable(x), None),
            ConfigOption('remote_mkdir', default=['/bin/mkdir', '-p']): list,
            ConfigOption('testplan_path', default=None): Or(str, None),
            ConfigOption('worker_heartbeat', default=30): Or(int, float, None)
        }


class RemotePool(Pool):
    """
    Pool task executor object that initializes remote workers and dispatches
    tasks.
    """

    CONFIG = RemotePoolConfig
    CONN_MANAGER = TCPConnectionManager

    def _add_workers(self):
        """TODO."""
        for host, workers in self.cfg.hosts.items():
            worker = self.cfg.worker_type(
                index=host, workers=workers, pool_type=self.cfg.pool_type)
            self.logger.debug('Created {}'.format(worker))
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=host)
            # print('Added worker with id {}'.format(idx))
            self._conn.register(worker)
