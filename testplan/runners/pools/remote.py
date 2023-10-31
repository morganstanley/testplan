"""Remote worker pool module."""

import os
import signal
import socket
from multiprocessing.pool import ThreadPool
from typing import List, Dict, Tuple, Callable, Type, Union

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.remote.remote_resource import (
    RemoteResourceConfig,
    RemoteResource,
    UnboundRemoteResourceConfig,
)
from testplan.common.report.base import EventRecorder
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.path import rebase_path
from testplan.common.utils.remote import ssh_cmd, copy_cmd
from testplan.common.utils.timing import get_sleeper, wait
from .base import Pool, PoolConfig
from .communication import Message
from .connection import ZMQServer
from .process import ProcessWorker, ProcessWorkerConfig


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
    :param workers: Number of thread/process workers of the child
    pool, default to 1.

    Also inherits all
    :py:class:`~testplan.runners.pools.process.ProcessWorkerConfig` and
    :py:class:`~testplan.common.remote.remote_resource.RemoteResource`
    options.
    """

    CONFIG = RemoteWorkerConfig

    def __init__(self, **options) -> None:
        if options["workers"] == 1:
            options["pool_type"] = "thread"
        super().__init__(**options)

    def _set_child_script(self) -> None:
        """Specify the remote worker executable file."""
        self._child_paths.local = self._child_path()
        self._child_paths.remote = rebase_path(
            self._child_paths.local,
            self._testplan_import_path.local,
            self._testplan_import_path.remote,
        )

    def _proc_cmd_impl(self) -> List[str]:

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

    def _proc_cmd(self) -> str:
        """Command to start child process."""

        cmd = self._proc_cmd_impl()
        return self.cfg.ssh_cmd(self.ssh_cfg, " ".join(cmd))

    def _write_syspath(self) -> None:
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

    def pre_start(self) -> None:
        self.define_runpath()
        with EventRecorder(
            name="Prepare remote", event_type="function"
        ) as event_executor:
            self._prepare_remote()
        self.event_recorder.add_child(event_executor)
        self._set_child_script()
        self._write_syspath()

    def pre_stop(self) -> None:
        """Stop child process worker."""
        with EventRecorder(
            name="Fetch results", event_type="function"
        ) as event_executor:
            self._fetch_results()
        self.event_recorder.add_child(event_executor)

    def post_stop(self) -> None:
        self._clean_remote()

    def _wait_stopped(self, timeout: float = None) -> None:
        sleeper = get_sleeper(1, timeout)
        while next(sleeper):
            if self.status != self.status.STOPPED:
                self.logger.info("Waiting for workers to stop")
            else:
                self.post_stop()
                break
        else:
            msg = f"Not able to stop worker {self} after {timeout}s"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def _rebase_assertion(self, result) -> None:
        if isinstance(result, dict) and "source_path" in result:
            result["source_path"] = rebase_path(
                result["source_path"],
                self._remote_plan_runpath,
                self._get_plan().runpath,
            )
        else:
            entries = getattr(result, "entries", [])
            for entry in entries:
                self._rebase_assertion(entry)

    def rebase_attachment(self, result) -> None:
        """Rebase the path of attachment from remote to local"""

        if result:
            for attachment in result.report.attachments:
                attachment.source_path = rebase_path(
                    attachment.source_path,
                    self._remote_plan_runpath,
                    self._get_plan().runpath,
                )
            self._rebase_assertion(result.report)

    def rebase_task_path(self, task) -> None:
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
    :param hosts: Map of host(ip): number of their local thread/process workers.
        i.e {'hostname1': 2, '10.147.XX.XX': 4}
    :param abort_signals: Signals to trigger abort logic. Default: INT, TERM.
    :param worker_type: Type of worker to be initialized.
    :param pool_type: Child pool type that remote workers will use.
    can be ``thread`` or ``process``, default to ``thread`` if
    ``workers`` is 1 and otherwise ``process``.
    :param host: Host that pool binds and listens for requests. Defaults to
        local hostname.
    :param port: Port that pool binds. Default: 0 (random)
    :param worker_heartbeat: Worker heartbeat period.
    :param ssh_port: The ssh port number of remote host, default is 22.
    :param ssh_cmd: callable that prefix a command with ssh binary and options
    :param copy_cmd: callable that returns the cmdline to do copy on remote host
    :param workspace: Current project workspace to be transferred, default is pwd.
    :param workspace_exclude: Patterns to exclude files when pushing workspace.
    :param remote_runpath: Root runpath on remote host, default is same as local (Linux->Linux)
      or /var/tmp/$USER/testplan/$plan_name (Window->Linux).
    :param testplan_path: Path to import testplan from on remote host,
      default is testplan_lib under remote_runpath
    :param remote_workspace: The path of the workspace on remote host,
      default is fetched_workspace under remote_runpath
    :param clean_remote: Deleted root runpath on remote at exit.
    :param push: Files and directories to push to the remote.
    :type push: ``list`` that contains ``str`` or ``tuple``:
        - ``str``: Name of the file or directory
        - ``tuple``: A (src, dst) pair
    :param push_exclude: Patterns to exclude files on push stage.
    :param delete_pushed: Deleted pushed files on remote at exit.
    :param fetch_runpath: The flag of fetch remote resource's runpath, default to True.
    :param fetch_runpath_exclude: Exclude files matching PATTERN.
    :param pull: Files and directories to be pulled from the remote at the end.
    :param pull_exclude: Patterns to exclude files on pull stage..
    :param env: Environment variables to be propagated.
    :param setup_script: Script to be executed on remote as very first thing.

    Also inherits all :py:class:`~testplan.runner.pools.base.Pool` options.
    """

    CONFIG = RemotePoolConfig
    CONN_MANAGER = ZMQServer

    def __init__(
        self,
        name: str,
        hosts: Dict[str, int],
        abort_signals: List[int] = None,
        worker_type: Type = RemoteWorker,
        pool_type: str = "process",
        host: str = CONFIG.default_hostname,
        port: int = 0,
        worker_heartbeat: float = 30,
        ssh_port: int = 22,
        ssh_cmd: Callable = ssh_cmd,
        copy_cmd: Callable = copy_cmd,
        workspace: str = None,
        workspace_exclude: List[str] = None,
        remote_runpath: str = None,
        testplan_path: str = None,
        remote_workspace: str = None,
        clean_remote: bool = False,
        push: List[Union[str, Tuple[str, str]]] = None,
        push_exclude: List[str] = None,
        delete_pushed: bool = False,
        fetch_runpath: bool = True,
        fetch_runpath_exclude: List[str] = None,
        pull: List[str] = None,
        pull_exclude: List[str] = None,
        env: Dict[str, str] = None,
        setup_script: List[str] = None,
        **options,
    ) -> None:
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
    def _worker_setup_metadata(worker, request, response) -> None:
        worker.respond(
            response.make(Message.Metadata, data=worker.setup_metadata)
        )

    def _add_workers(self) -> None:
        """TODO."""
        for instance in self._instances.values():
            worker = self.cfg.worker_type(
                index=instance["host"],
                remote_host=instance["host"],
                workers=instance["number_of_workers"],
                **self._options,
            )
            self.logger.debug("Created %s", worker)
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=instance["host"])

    def _start_workers(self) -> None:
        """Start all workers of the pool"""
        for worker in self._workers:
            self._conn.register(worker)
        if self.pool:
            self._workers.start_in_pool(self.pool)
        else:
            self._workers.start()

    def _stop_workers(self) -> None:
        if self.pool:
            self._workers.stop_in_pool(self.pool)
        else:
            self._workers.stop()

    def _start_thread_pool(self) -> None:
        size = len(self._instances)
        try:
            if size > 2:
                self.pool = ThreadPool(5 if size > 5 else size)
        except Exception as exc:
            if isinstance(exc, AttributeError):
                self.logger.warning(
                    "Please upgrade to the suggested python interpreter."
                )

    def starting(self) -> None:
        self._start_thread_pool()
        super(RemotePool, self).starting()

    def stopping(self) -> None:
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
                        "Timeout waiting for worker %s to quit starting "
                        "while pool %s is stopping",
                        worker,
                        self.cfg.name,
                    )

        super(RemotePool, self).stopping()

        if self.pool:
            self.pool.terminate()
            self.pool = None

    def aborting(self) -> None:
        """Aborting logic."""

        super(RemotePool, self).aborting()

        if self.pool:
            self.pool.terminate()
            self.pool = None

    def get_current_status_for_debug(self) -> List[str]:
        """
        Gets ``Hosts`` and ``Workers`` infromation for debugging.

        :return: Status information of Hosts and Workers.
        """
        msgs = [f"Hosts and number of workers in {self.class_name}:"]

        for host, number_of_workers in self.cfg.hosts.items():
            msgs.append(
                f"\t Host: {host}, Number of workers: {number_of_workers}"
            )

        msgs.extend(super().get_current_status_for_debug())
        return msgs
