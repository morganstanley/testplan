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
from testplan.runners.pools import child


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


class _LocationPaths(object):
    """Store local and remote equivalent paths."""

    def __init__(self):
        self.local = None
        self.remote = None


class RemoteWorker(ProcessWorker):
    """
    Remote worker resource that pulls tasks from the transport provided,
    executes them in a local pool of workers and sends back task results.
    """

    CONFIG = RemoteWorkerConfig

    def __init__(self, **options):
        super(RemoteWorker, self).__init__(**options)
        self._remote_base_path = None
        self._user = getpass.getuser()
        self._workspace_paths = _LocationPaths()
        self._child_paths = _LocationPaths()
        self._testplan_paths = _LocationPaths()
        self._working_dirs = _LocationPaths()
        self._should_transfer_workspace = True
        self._remote_testplan_runpath = None
        self.setup_metadata = WorkerSetupMetadata()

    def _execute_cmd(self, cmd, label=None, check=True):
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

        # Check the return-code. By default we expect commands to return 0,
        # check can be set to False if it is expected that commands may return
        # non-zero exit codes.
        if check and handler.returncode != 0:
            raise RuntimeError(
                'Remote command {cmd} exited with non-zero exit code {rc}'
                .format(cmd=cmd, rc=handler.returncode))

        return handler.returncode

    def _define_remote_dirs(self):
        """Define mandatory directories in remote host."""
        testplan_path_dirs = ['', 'var', 'tmp', getpass.getuser(), 'testplan']
        self._remote_base_path = '/'.join(
            testplan_path_dirs + ['remote_workspaces',
                                  slugify(self.cfg.parent.parent.name)])
        self._remote_testplan_runpath = '/'.join(
            [self._remote_base_path, 'runpath', str(self.cfg.index)])

    def _create_remote_dirs(self):
        """Create mandatory directories in remote host."""
        cmd = self.cfg.remote_mkdir + [self._remote_base_path]
        self._execute_cmd(
            self.cfg.ssh_cmd(self.cfg.index, ' '.join([str(a) for a in cmd])),
            label='create remote dirs')

    def _copy_dependencies_modules(self):
        """Copy mandatory dependencies need to be imported before testplan."""
        path = os.environ.get('TESTPLAN_DEPENDENCIES_PATH')
        if path is None:
            return
        self.logger.debug('Copying deps from path %s', path)

        # Copy over the dependencies module.
        filename = 'dependencies.py'
        local_deps_path = '/'.join((path, filename))
        remote_deps_path = '/'.join((self._remote_base_path, filename))
        self._transfer_data(
            source=local_deps_path,
            target=remote_deps_path,
            remote_target=True)

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
                target=os.path.dirname(_dir),
                remote_target=True,
                exclude=self.cfg.push_exclude)
        for _file in push_files:
            dirname = '/'.join(os.path.dirname(_file).split(os.sep))
            cmd = self.cfg.remote_mkdir + [dirname]
            self._execute_cmd(self.cfg.ssh_cmd(
                self.cfg.index, ' '.join([str(a) for a in cmd])),
                label='create empty file dir')
            self._transfer_data(
                source=_file,
                target='/'.join(os.path.dirname(_file).split(os.sep)),
                remote_target=True,
                exclude=self.cfg.push_exclude)

    def _copy_workspace(self):
        """Copy the local workspace to remote host."""
        self._transfer_data(
            source=self._workspace_paths.local,
            target=self._remote_base_path,
            remote_target=True,
            exclude=self.cfg.workspace_exclude)
        self._workspace_paths.remote = '{}/{}'.format(
            self._remote_base_path,
            self._workspace_paths.local.split(os.sep)[-1])
        self.logger.debug('Remote workspace = %s',
                          self._workspace_paths.remote)

    def _transfer_data(self,
                       source,
                       target,
                       remote_source=False,
                       remote_target=False,
                       check=True,
                       **copy_args):
        """
        Copy files or directories. Set remote_source and/or remote_target to
        True to copy from/to paths on the remote host.
        """
        def _remote_copy_path(path):
            """
            Return a path on the remote host in the format user@host:path,
            suitable for use in a copy command such as `scp`.
            """
            return '{user}@{host}:{path}'.format(
                user=self._user, host=self.cfg.index, path=path)

        if remote_source:
            source = _remote_copy_path(source)
        if remote_target:
            target = _remote_copy_path(target)
        self.logger.debug('Copying %(source)s to %(target)s', locals())
        cmd = self.cfg.copy_cmd(source, target, **copy_args)
        self._execute_cmd(cmd, 'transfer data [..{}]'.format(
            os.path.basename(target)), check=check)

    def _remote_filepath_exists(self, filepath):
        """
        :return: whether a filepath exists on the remote host.
        :rtype: bool
        """
        cmd = remote_filepath_exists(self.cfg.ssh_cmd,
                                     self.cfg.index,
                                     filepath)
        return self._execute_cmd(
            cmd, label='remote filepath check', check=False) == 0

    def _define_local_paths(self):
        self._child_paths.local = module_abspath(child, self._user)
        self._working_dirs.local = pwd()
        self._workspace_paths.local = self.cfg.workspace
        self._testplan_paths.local = os.path.dirname(
            module_abspath(testplan, self._user))
        self.logger.info('Local testplan path = %s', self._testplan_paths.local)

    def _set_remote_testplan_path(self):
        """
        Check and set the remote testplan package path. The package will be
        transferred from the local host if required.
        """
        if self._remote_filepath_exists(self._testplan_paths.local):
            self._testplan_paths.remote = self._testplan_paths.local
        else:
            self._testplan_paths.remote = '/'.join((self._remote_base_path,
                                                    'testplan'))
            # To save multiple uploads, only transfer the package if it is not
            # already present on the remote host.
            if not self._remote_filepath_exists(self._testplan_paths.remote):
                self.logger.debug('Copying testplan package to remote host...')
                self._transfer_data(
                    source=self._testplan_paths.local,
                    target=self._remote_base_path,
                    remote_target=True)
        self.logger.debug('Testplan package on remote host at: %s',
                          self._testplan_paths.remote)

    def _set_remote_child_path(self):
        """
        Set the path to the remote child script. It should already exist under
        the testplan package.
        """
        self._child_paths.remote = '/'.join((self._testplan_paths.remote,
                                             'runners',
                                             'pools',
                                             'child.py'))
        assert self._remote_filepath_exists(self._child_paths.remote)

    def _set_remote_workspace_path(self):
        """
        Set the remote workspace path, transferring the local workspace over
        if required. The workspace represents the tests we are running and their
        dependencies.
        """
        # Check if the workspace needs transferring to the remote host.
        if self.cfg.copy_workspace_check:
            self.logger.debug('Checking if we should copy workspace at %s',
                              self._workspace_paths.local)
            cmd = self.cfg.copy_workspace_check(
                self.cfg.ssh_cmd,
                self.cfg.index,
                self._workspace_paths.local)
            self._should_transfer_workspace = self._execute_cmd(
                cmd, label='copy workspace check', check=False) != 0
        else:
            self.logger.warning('Not checking - just copying workspace.')

        # Transfer workspace if required and set the remote workspace path.
        if self._should_transfer_workspace:
            self.logger.debug('Copying over workspace...')
            if self.cfg.remote_workspace:
                self._workspace_paths.remote = self.cfg.remote_workspace
            else:
                self._copy_workspace()
                # Mark that workspace pushed is safe to delete. Not some NFS.
                self.setup_metadata.workspace_pushed = True
        else:
            self.logger.debug('Workspace already present on remote host.')
            self._workspace_paths.remote = self._workspace_paths.local

    def _prepare_remote(self):
        """Transfer local data to remote host."""
        self._define_local_paths()

        # Define and create required remote directories.
        self._define_remote_dirs()
        self._create_remote_dirs()

        # Ensure that the testplan package is available on the remote.
        self._set_remote_testplan_path()

        # Ensure the remote child script is present.
        self._set_remote_child_path()

        # Copy the dependencies modules.
        self._copy_dependencies_modules()

        # Ensure that the current workspace is available on the remote.
        self._set_remote_workspace_path()

        # Set the remote working directory.
        self._working_dirs.remote = '{}{}'.format(
            self._workspace_paths.remote,
            '/'.join(pwd().split(os.sep)).replace(
                '/'.join(self._workspace_paths.local.split(os.sep)),
                ''))

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
                    source=entry,
                    remote_source=True,
                    target=dirname,
                    exclude=self.cfg.pull_exclude)

    def _fetch_results(self):
        """Fetch back to local host the results generated remotely."""
        self.logger.debug('Fetch results stage - {}'.format(self.cfg.index))
        self._transfer_data(
            source=self._remote_testplan_runpath,
            remote_source=True,
            target=self.parent.runpath)

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
               self._child_paths.remote,
               '--index', str(self.cfg.index),
               '--address', self.transport.address,
               '--type', 'remote_worker',
               '--log-level', str(TESTPLAN_LOGGER.getEffectiveLevel()),
               '--wd', self._working_dirs.remote,
               '--runpath', self._remote_testplan_runpath,
               '--remote-pool-type', self.cfg.pool_type,
               '--remote-pool-size', str(self.cfg.workers),
               '--testplan', self._testplan_paths.remote]
        if not self._should_transfer_workspace:
            self._add_testplan_deps_import_path(cmd, flag='--testplan-deps')
        ret_cmd = self.cfg.ssh_cmd(self.cfg.index, ' '.join(cmd))
        self.logger.debug('Starting child processes with command: %s', ret_cmd)
        return ret_cmd

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

