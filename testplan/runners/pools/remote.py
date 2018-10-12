"""Remote worker pool module."""

import os
import sys
import time
import signal
import socket
import getpass
import platform
import subprocess

from schema import Or

import testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.path import module_abspath, pwd, makedirs
from testplan.common.utils.strings import slugify
from testplan.common.utils.remote import (
    ssh_cmd, copy_cmd, remote_filepath_exists)

from .base import Pool, PoolConfig
from .process import ProcessWorker, ProcessWorkerConfig
from .connection import TCPConnectionManager
from .communication import Message


class WorkerSetupMetadata(object):
    """
    Metadata used on worker setup stage execution.
    Pushed dirs and files will be registered for deletion at exit.
    """

    def __init__(self):
        self.push_dirs = None
        self.push_files = None
        self.setup_script = None
        self.env = None
        self.workspace_paths = None
        self.workspace_pushed = False


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
        self._should_transfer_workspace = True
        self._remote_testplan_runpath = None
        self.setup_metadata = WorkerSetupMetadata()

    def _execute_cmd(self, cmd, label=None):
        """Execute a subprocess command."""
        self.logger.debug('Executing command{}: {}'.format(
            ' [{}]'.format(label) if label else '', cmd))
        start_time = time.time()
        handler = subprocess.Popen(
            [str(a) for a in cmd],
            stdout=sys.stdout, stderr=sys.stderr, stdin=subprocess.PIPE)
        handler.stdin.write(bytes('y\n'.encode('utf-8')))
        handler.wait()
        if label:
            self.logger.debug('Command [{}] finished in {}s.'.format(
                label, time.time()-start_time))
        return handler.returncode

    def _define_remote_dirs(self):
        """Define mandatory directories in remote host."""
        testplan_path_dirs = ['', 'var', 'tmp', getpass.getuser(), 'testplan']
        self._remote_testplan_path = '/'.join(
            testplan_path_dirs + ['remote_workspaces',
                                  slugify(self.cfg.parent.parent.name)])
        self._remote_testplan_runpath = '/'.join(
            [self._remote_testplan_path, 'runpath', str(self.cfg.index)])

    def _create_remote_dirs(self):
        """Create mandatory directories in remote host."""
        cmd = self.cfg.remote_mkdir + [self._remote_testplan_path]
        self._execute_cmd(
            self.cfg.ssh_cmd(self.cfg.index, ' '.join([str(a) for a in cmd])),
            label='create remote dirs')

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

    def _push_files(self):
        """Push files and directories to remote host."""
        if not self.cfg.push:
            return
        push_files = []
        push_dirs = []
        for item in self.cfg.push:
            item = item.rstrip(os.sep)
            if os.path.isfile(item):
                if item not in push_files:
                    push_files.append(item)
            elif os.path.isdir(item):
                if item not in push_dirs:
                    push_dirs.append(item)
            else:
                self.logger.error('Item "{}" cannot be pushed!'.format(item))

        # Eliminate push duplications
        if push_dirs and len(push_dirs) > 1:
            push_dirs.sort()
            for idx in range(len(push_dirs) - 1):
                if push_dirs[idx + 1].startswith(push_dirs[idx]):
                    push_dirs[idx] = None
            push_dirs = [_dir for _dir in push_dirs if _dir is not None]

        self.setup_metadata.push_dirs = ['/'.join(
            item.split(os.sep)) for item in push_dirs]
        self.setup_metadata.push_files = ['/'.join(
            item.split(os.sep)) for item in push_files]

        # Make parent dirs and copy data.
        # Since we are only transfering to linux platforms, we split with
        # possible windows path separator and join with linux.
        for _dir in push_dirs:
            dirname = '/'.join(os.path.dirname(_dir).split(os.sep))
            cmd = self.cfg.remote_mkdir + [dirname]
            self._execute_cmd(self.cfg.ssh_cmd(
                self.cfg.index, ' '.join([str(a) for a in cmd])),
                label='create push file dir')
            self._transfer_data(
                source=_dir,
                target='{}@{}:{}'.format(
                    self._user, self.cfg.index, os.path.dirname(_dir)),
                exclude=self.cfg.push_exclude)
        for _file in push_files:
            dirname = '/'.join(os.path.dirname(_file).split(os.sep))
            cmd = self.cfg.remote_mkdir + [dirname]
            self._execute_cmd(self.cfg.ssh_cmd(
                self.cfg.index, ' '.join([str(a) for a in cmd])),
                label='create empty file dir')
            self._transfer_data(
                source=_file,
                target='{}@{}:{}'.format(
                    self._user, self.cfg.index,
                    '/'.join(os.path.dirname(_file).split(os.sep))),
                exclude=self.cfg.push_exclude)

    def _copy_workspace(self):
        """Copy the local workspace to remote host."""
        self._transfer_data(
            source=self._workspace_paths['local'],
            target='{}@{}:{}'.format(
                self._user, self.cfg.index, self._remote_testplan_path),
            exclude=self.cfg.workspace_exclude)
        self._workspace_paths['remote'] = '{}/{}'.format(
            self._remote_testplan_path,
            self._workspace_paths['local'].split(os.sep)[-1])

    def _transfer_data(self, source, target, **copy_args):
        cmd = self.cfg.copy_cmd(source, target, **copy_args)
        self._execute_cmd(cmd, 'transfer data [..{}]'.format(
            os.path.basename(target)))

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
            self._should_transfer_workspace = self._execute_cmd(
                cmd, label='copy workspace check') != 0

        self._define_remote_dirs()

        if self._should_transfer_workspace is True:
            self._create_remote_dirs()
            self._copy_child_script()
            self._copy_dependencies_module()
            if self.cfg.remote_workspace:
                self._workspace_paths['remote'] = self.cfg.remote_workspace
            else:
                self._copy_workspace()
                # Mark that workspace pushed is safe to delete. Not some NFS.
                self.setup_metadata.workspace_pushed = True

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

        self._push_files()
        self.setup_metadata.setup_script = self.cfg.setup_script
        self.setup_metadata.env = self.cfg.env
        self.setup_metadata.workspace_paths = self._workspace_paths

    def _pull_files(self):
        """Push custom files to be available on remotes."""
        for entry in [itm.rstrip('/') for itm in self.cfg.pull]:
            # Prepare target path for possible windows usage.
            dirname = os.sep.join(os.path.dirname(entry).split('/'))
            try:
                makedirs(dirname)
            except Exception as exc:
                self.logger.error('Cound not create {} directory - {}'.format(
                    dirname, exc))
            else:
                self._transfer_data(
                    source='{}@{}:{}'.format(self._user, self.cfg.index, entry),
                    target=dirname,
                    exclude=self.cfg.pull_exclude)

    def _fetch_results(self):
        """Fetch back to local host the results generated remotely."""
        self.logger.debug('Fetch results stage - {}'.format(self.cfg.index))
        self._transfer_data(
            source='{}@{}:{}'.format(self._user, self.cfg.index,
                                     self._remote_testplan_runpath),
            target=self.parent.runpath)

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
               '--runpath', self._remote_testplan_runpath,
               '--remote-pool-type', self.cfg.pool_type,
               '--remote-pool-size', str(self.cfg.workers)]
        self._add_testplan_import_path(cmd, flag='--testplan')
        if not self._should_transfer_workspace:
            self._add_testplan_deps_import_path(cmd, flag='--testplan-deps')
        return self.cfg.ssh_cmd(self.cfg.index, ' '.join(cmd))

    def starting(self):
        """Start a child remote worker."""
        self._prepare_remote()
        super(RemoteWorker, self).starting()

    def stopping(self):
        """Stop child process worker."""
        self._fetch_results()
        if self.cfg.pull:
            self._pull_files()
        super(RemoteWorker, self).stopping()

    def aborting(self):
        """Abort child process worker."""
        try:
            self._fetch_results()
        except Exception as exc:
            self.logger.error('Could not fetch results, {}'.format(exc))
        super(RemoteWorker, self).aborting()


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
    :param workspace_exclude: Patterns to exclude files when pushing workspace.
    :type workspace_exclude: ``list`` of ``str``
    :param remote_workspace: Use a workspace that already exists in remote host.
    :type remote_workspace: ``str``
    :param copy_workspace_check: Check to indicate whether to copy workspace.
    :type copy_workspace_check: ``callable`` or ``NoneType``
    :param env: Environment variables to be propagated.
    :type env: ``dict``
    :param setup_script: Script to be executed on remote as very first thing.
    :type setup_script: ``list`` of ``str``
    :param push: Files and directories to push to the remote.
    :type push: ``list`` of ``str``
    :param push_exclude: Patterns to exclude files on push stage.
    :type push_exclude: ``list`` of ``str``
    :param delete_pushed: Deleted pushed files and workspace on remote at exit.
    :type delete_pushed: ``bool``
    :param pull: Files and directories to be pulled from the remote at the end.
    :type pull: ``list`` of ``str``
    :param pull_exclude: Patterns to exclude files on pull stage..
    :type pull_exclude: ``list`` of ``str``
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
            ConfigOption('workspace_exclude', default=[]): Or(list, None),
            ConfigOption('remote_workspace', default=None): Or(str, None),
            ConfigOption('copy_workspace_check',
                         default=remote_filepath_exists):
                Or(lambda x: callable(x), None),
            ConfigOption('env', default=None): Or(dict, None),
            ConfigOption('setup_script', default=None): Or(list, None),
            ConfigOption('push', default=[]): Or(list, None),
            ConfigOption('push_exclude', default=[]): Or(list, None),
            ConfigOption('delete_pushed', default=False): bool,
            ConfigOption('pull', default=[]): Or(list, None),
            ConfigOption('pull_exclude', default=[]): Or(list, None),
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

    def __init__(self, **options):
        super(RemotePool, self).__init__(**options)
        self._request_handlers[Message.MetadataPull] =\
            self._worker_setup_metadata

    @staticmethod
    def _worker_setup_metadata(worker, response):
        worker.respond(response.make(
            Message.Metadata, data=worker.setup_metadata))

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
