"""Remote worker pool module."""

import os
import signal
import socket
from multiprocessing.pool import ThreadPool

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.remote.remote_resource import (
    RemoteResourceConfig,
    RemoteResource,
    UnboundRemoteResourceConfig,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.path import (
    rebase_path,
)
from testplan.common.utils.remote import ssh_cmd, copy_cmd
from testplan.common.utils.timing import wait
from testplan.runners.pools.base import Pool, PoolConfig
from testplan.runners.pools.communication import Message
from testplan.runners.pools.connection import ZMQServer
from testplan.runners.pools.process import ProcessWorker, ProcessWorkerConfig


class UnboundRemoteWorkerConfig(
    ProcessWorkerConfig, UnboundRemoteResourceConfig
):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.remote.RemoteWorker` resource entity.
    """

    # RemoteWorker will receive params passed to RemotePool
    # thus allow extra keys
    ignore_extra_keys = True

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {"workers": int, "pool_type": str}


class RemoteWorkerConfig(UnboundRemoteWorkerConfig, RemoteResourceConfig):
    pass


class RemoteWorker(ProcessWorker, RemoteResource):
    """
    Remote worker resource that pulls tasks from the transport provided,
    executes them in a local pool of workers and sends back task results.

    :param pool_type: Child pool type that remote workers will use.
    can be ``thread`` or ``process``, default to ``thread`` if
    ``workers`` is 1 and otherwise ``process``.
    :type pool_type: ``str``
    :param workers: Number of thread/process workers of the child
    pool, default to 1.
    :type workers: ``int``

    Also inherits all
    :py:class:`~testplan.runners.pools.process.ProcessWorkerConfig` and
    :py:class:`~testplan.common.remote.remote_resource.RemoteResource`
    options.
    """

    CONFIG = RemoteWorkerConfig

    def __init__(self, **options):
        if options["workers"] == 1:
            options["pool_type"] = "thread"
        super().__init__(**options)

    def _set_child_script(self):
        """Specify the remote worker executable file."""
        self._child_paths.local = self._child_path()
        self._child_paths.remote = rebase_path(
            self._child_paths.local,
            self._testplan_import_path.local,
            self._testplan_import_path.remote,
        )

    def _proc_cmd_impl(self):

        cmd = [
            self.python_binary,
            "-uB",
            self._child_paths.remote,
            "--index",
            str(self.cfg.index),
            "--address",
            self.transport.address,
            "--type",
            "remote_worker",
            "--log-level",
            str(TESTPLAN_LOGGER.getEffectiveLevel()),
            "--wd",
            self._working_dirs.remote,
            "--runpath",
            self._remote_resource_runpath,
            "--remote-pool-type",
            self.cfg.pool_type,
            "--remote-pool-size",
            str(self.cfg.workers),
            "--sys-path-file",
            self._remote_syspath_file,
        ]

        return cmd

    def _proc_cmd(self):
        """Command to start child process."""

        cmd = self._proc_cmd_impl()
        return self.cfg.ssh_cmd(self.ssh_cfg, " ".join(cmd))

    def _write_syspath(self):
        """
        Write our current sys.path to a file and transfer it to the remote
        host.
        """
        super(RemoteWorker, self)._write_syspath(
            sys_path=self._remote_sys_path()
        )
        self._remote_syspath_file = os.path.join(
            self._remote_plan_runpath,
            f"sys_path_{os.path.basename(self._syspath_file)}",
        )
        self._transfer_data(
            source=self._syspath_file,
            target=self._remote_syspath_file,
            remote_target=True,
        )

        self.logger.debug(
            "Transferred sys.path to remote host at: %s",
            self._remote_syspath_file,
        )

    def pre_start(self):
        self.define_runpath()
        self._prepare_remote()
        self._set_child_script()
        self._write_syspath()

    def pre_stop(self):
        self._fetch_results()

    def post_stop(self):
        self._clean_remote()

    def aborting(self):
        """Remote worker abort logic."""
        self._transport.disconnect()
        self.pre_stop()
        self.stopping()
        self.post_stop()

    def rebase_attachment(self, result):
        """Rebase the path of attachment from remote to local"""

        if result:
            for attachment in result.report.attachments:
                attachment.source_path = rebase_path(
                    attachment.source_path,
                    self._remote_plan_runpath,
                    self._get_plan().runpath,
                )

    def rebase_task_path(self, task):
        """Rebase the path of task from local to remote"""
        task.rebase_path(
            self._workspace_paths.local, self._workspace_paths.remote
        )


class RemotePoolConfig(PoolConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.remote.RemotePool` executor
    resource entity.
    """

    # RemotePool is taking param that are to be passed to RemoteWorker
    # thus allow extra keys
    ignore_extra_keys = True

    default_hostname = socket.gethostbyname(socket.gethostname())

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "hosts": dict,
            ConfigOption(
                "abort_signals", default=[signal.SIGINT, signal.SIGTERM]
            ): [int],
            ConfigOption("worker_type", default=RemoteWorker): object,
            ConfigOption("pool_type", default="process"): str,
            ConfigOption("host", default=cls.default_hostname): str,
            ConfigOption("port", default=0): int,
            ConfigOption("worker_heartbeat", default=30): Or(int, float, None),
        }


class RemotePool(Pool):
    """
    Pool task executor object that initializes remote workers and dispatches
    tasks.

    :param name: Pool name.
    :type name: ``str``
    :param hosts: Map of host(ip): number of their local thread/process workers.
        i.e {'hostname1': 2, '10.147.XX.XX': 4}
    :type hosts: ``dict`` of ``str``:``int``
    :param abort_signals: Signals to trigger abort logic. Default: INT, TERM.
    :type abort_signals: ``list`` of ``int``
    :param worker_type: Type of worker to be initialized.
    :type worker_type: :py:class:`~testplan.runners.pools.remote.RemoteWorker`
    :param pool_type: Child pool type that remote workers will use.
    can be ``thread`` or ``process``, default to ``thread`` if
    ``workers`` is 1 and otherwise ``process``.
    :type pool_type: ``str``
    :param host: Host that pool binds and listens for requests. Defaults to
        local hostname.
    :type host: ``str``
    :param port: Port that pool binds. Default: 0 (random)
    :type port: ``int``
    :param worker_heartbeat: Worker heartbeat period.
    :type worker_heartbeat: ``int`` or ``float`` or ``NoneType``

    :param ssh_port: The ssh port number of remote host, default is 22.
    :type ssh_port: ``int``
    :param ssh_cmd: callable that prefix a command with ssh binary and options
    :param ssh_cmd: ``callable``
    :param copy_cmd: callable that returns the cmdline to do copy on remote host
    :type copy_cmd: ``callable``

    :param workspace: Current project workspace to be transferred, default is pwd.
    :type workspace: ``str``
    :param workspace_exclude: Patterns to exclude files when pushing workspace.
    :type workspace_exclude: ``list`` of ``str``

    :param remote_runpath: Root runpath on remote host, default is same as local (Linux->Linux)
      or /var/tmp/$USER/testplan/$plan_name (Window->Linux).
    :type remote_runpath: ``str``
    :param testplan_path: Path to import testplan from on remote host,
      default is testplan_lib under remote_runpath
    :type testplan_path: ``str``
    :param remote_workspace: The path of the workspace on remote host,
      default is fetched_workspace under remote_runpath
    :type remote_workspace: ``str``
    :param clean_remote: Deleted root runpath on remote at exit.
    :type clean_remote: ``bool``

    :param push: Files and directories to push to the remote.
    :type push: ``list`` that contains ``str`` or ``tuple``:
        - ``str``: Name of the file or directory
        - ``type``: A (src, dst) pair
    :param push_exclude: Patterns to exclude files on push stage.
    :type push_exclude: ``list`` of ``str``
    :param delete_pushed: Deleted pushed files on remote at exit.
    :type delete_pushed: ``bool``

    :param fetch_runpath: The flag of fetch remote resource's runpath, default to True.
    :type fetch_runpath: ``bool``
    :param fetch_runpath_exclude: Exclude files matching PATTERN.
    :type fetch_runpath_exclude: ``list``

    :param pull: Files and directories to be pulled from the remote at the end.
    :type pull: ``list`` of ``str``
    :param pull_exclude: Patterns to exclude files on pull stage..
    :type pull_exclude: ``list`` of ``str``

    :param env: Environment variables to be propagated.
    :type env: ``dict``
    :param setup_script: Script to be executed on remote as very first thing.
    :type setup_script: ``list`` of ``str``

    Also inherits all :py:class:`~testplan.runner.pools.base.Pool` options.
    """

    CONFIG = RemotePoolConfig
    CONN_MANAGER = ZMQServer

    def __init__(
        self,
        name,
        hosts,
        abort_signals=None,
        worker_type=RemoteWorker,
        pool_type="process",
        host=CONFIG.default_hostname,
        port=0,
        worker_heartbeat=30,
        ssh_port=22,
        ssh_cmd=ssh_cmd,
        copy_cmd=copy_cmd,
        workspace=None,
        workspace_exclude=None,
        remote_runpath=None,
        testplan_path=None,
        remote_workspace=None,
        clean_remote=False,
        push=None,
        push_exclude=None,
        delete_pushed=False,
        fetch_runpath=True,
        fetch_runpath_exclude=None,
        pull=None,
        pull_exclude=None,
        env=None,
        setup_script=None,
        **options,
    ):
        self.pool = None
        options.update(self.filter_locals(locals()))
        super(RemotePool, self).__init__(**options)
        self._options = options  # pass to remote worker later

        self._request_handlers[
            Message.MetadataPull
        ] = self._worker_setup_metadata

        self._instances = {}

        for host, number_of_workers in self.cfg.hosts.items():
            self._instances[host] = {
                "host": host,
                "number_of_workers": number_of_workers,
            }

    @staticmethod
    def _worker_setup_metadata(worker, request, response):
        worker.respond(
            response.make(Message.Metadata, data=worker.setup_metadata)
        )

    def _add_workers(self):
        """TODO."""
        for instance in self._instances.values():
            worker = self.cfg.worker_type(
                index=instance["host"],
                remote_host=instance["host"],
                workers=instance["number_of_workers"],
                **self._options,
            )
            self.logger.debug("Created {}".format(worker))
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=instance["host"])

    def _start_workers(self):
        """Start all workers of the pool"""
        for worker in self._workers:
            self._conn.register(worker)

        if self.pool:
            self._workers.start_in_pool(self.pool)
        else:
            self._workers.start()

    def _stop_workers(self):
        if self.pool:
            self._workers.stop_in_pool(self.pool)
        else:
            self._workers.stop()

        for worker in self._workers:
            worker.transport.disconnect()

    def _start_thread_pool(self):
        size = len(self._instances)
        try:
            if size > 2:
                self.pool = ThreadPool(5 if size > 5 else size)
        except Exception as exc:
            if isinstance(exc, AttributeError):
                self.logger.warning(
                    "Please upgrade to the suggested python interpreter."
                )

    def starting(self):
        self._start_thread_pool()
        super(RemotePool, self).starting()

    def stopping(self):
        for worker in self._workers:
            if worker.status == worker.status.STARTING:
                try:
                    wait(
                        lambda: worker.status
                        in (worker.STATUS.STARTED, worker.STATUS.STOPPED),
                        worker.cfg.status_wait_timeout,
                    )
                except Exception:
                    self.logger.error(
                        "Timeout waiting for worker %s to quit starting"
                        " while pool %s is stopping",
                        worker,
                        self.cfg.name,
                    )

        super(RemotePool, self).stopping()

        if self.pool:
            self.pool.terminate()
            self.pool = None

    def aborting(self):
        """Aborting logic."""

        super(RemotePool, self).aborting()

        if self.pool:
            self.pool.terminate()
            self.pool = None
