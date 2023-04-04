"""Process worker pool module."""

import os
import re
import sys
import signal
import subprocess
import tempfile
from typing import List, Type, Union

from schema import Or

from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.config import ConfigOption
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.process import kill_process
from testplan.common.utils.timing import get_sleeper
from . import tasks
from .base import Pool, PoolConfig, Worker, WorkerConfig
from .connection import ZMQClientProxy, ZMQServer


class ProcessWorkerConfig(WorkerConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.process.ProcessWorker` resource entity.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption("transport", default=ZMQClientProxy): object,
            ConfigOption("sigint_timeout", default=5): int,
        }


class ProcessWorker(Worker):
    """
    Process worker resource that pulls tasks from the transport provided,
    executes them and sends back task results.

    :param transport: Transport class for pool/worker communication.
    :param sigint_timeout: number of seconds to wait between ``SIGINT`` and ``SIGKILL``

    Also inherits all :py:class:`~testplan.runners.pools.base.Worker` options.
    """

    CONFIG = ProcessWorkerConfig

    def __init__(
        self,
        sigint_timeout: int = 5,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        super(ProcessWorker, self).__init__(**options)

    def _child_path(self) -> str:
        dirname = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(dirname, "child.py")

    def _proc_cmd(self) -> List[str]:
        """Command to start child process."""
        from testplan.common.utils.path import fix_home_prefix

        cmd = [
            sys.executable,
            fix_home_prefix(self._child_path()),
            "--index",
            self.cfg.index,
            "--address",
            self.transport.address,
            "--type",
            "process_worker",
            "--log-level",
            TESTPLAN_LOGGER.getEffectiveLevel(),
            "--sys-path-file",
            self._syspath_file,
        ]

        return cmd

    def _write_syspath(self, sys_path: str = None) -> None:
        """Write out our current sys.path to a file and return the filename."""
        sys_path = sys_path or sys.path
        with tempfile.NamedTemporaryFile(
            mode="w", dir=self.parent.runpath, delete=False
        ) as f:
            f.write("\n".join(sys_path))
            self.logger.debug("Written sys.path to file: %s", f.name)
            self._syspath_file = f.name

    def pre_start(self) -> None:
        self._write_syspath()

    def starting(self) -> None:
        """Start a child process worker."""
        # NOTE: Worker resource has no runpath.
        cmd = self._proc_cmd()
        self.logger.debug("%s executes cmd: %s", self, cmd)

        with open(self.outfile, "wb") as out:
            self._handler = subprocess.Popen(
                [str(a) for a in cmd],
                stdout=out,
                stderr=out,
                stdin=subprocess.PIPE,
            )
        self.logger.debug("Started child process - output at %s", self.outfile)
        self._handler.stdin.write(bytes("y\n".encode("utf-8")))

    def _wait_started(self, timeout: float = None) -> None:
        """"""
        sleeper = get_sleeper(
            interval=(0.04, 0.5),
            timeout=timeout,
            raise_timeout_with_msg=f"Worker start timeout, logfile = {self.outfile}",
        )
        while next(sleeper):
            if match_regexps_in_file(
                self.outfile, [re.compile("Starting child process worker on")]
            )[0]:
                super(ProcessWorker, self)._wait_started(timeout=timeout)
                return

            if self._handler and self._handler.poll() is not None:
                raise RuntimeError(
                    f"{self} process exited: {self._handler.returncode}"
                    f" (logfile = {self.outfile})"
                )

    @property
    def is_alive(self) -> bool:
        if self._handler is None:
            self.logger.debug("No worker process started")
            return False

        # Check if the child process already terminated.
        if self._handler.poll() is not None:
            self.logger.critical(
                "Worker process exited with code %d", self._handler.returncode
            )
            self._handler = None
            return False
        else:
            return True

    def stopping(self) -> None:
        """Stop child process worker."""
        if hasattr(self, "_handler") and self._handler:
            kill_process(self._handler, self.cfg.sigint_timeout)
        self.status.change(self.STATUS.STOPPED)

    def aborting(self) -> None:
        """Process worker abort logic."""
        self._transport.disconnect()
        self.stop()


class ProcessPoolConfig(PoolConfig):
    """
    Configuration object for
    :py:class:`~testplan.runners.pools.process.ProcessPool` executor
    resource entity.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            ConfigOption("host", default="127.0.0.1"): str,
            ConfigOption("port", default=0): int,
            ConfigOption(
                "abort_signals", default=[signal.SIGINT, signal.SIGTERM]
            ): [int],
            ConfigOption("worker_type", default=ProcessWorker): object,
            ConfigOption("worker_heartbeat", default=5): Or(int, float, None),
        }


class ProcessPool(Pool):
    """
    Pool task executor object that initializes process workers and dispatches
    tasks.

    :param name: Pool name.
    :param size: Pool workers size. If you set size="auto",
        smart-scheduling feature will calculate the size. Default: 4
    :param host: Host that pool binds and listens for requests.
    :param port: Port that pool binds. Default: 0 (random)
    :param abort_signals: Signals to trigger abort logic. Default: INT, TERM.
    :param worker_type: Type of worker to be initialized.
    :param worker_heartbeat: Worker heartbeat period.

    Also inherits all :py:class:`~testplan.runners.pools.base.Pool` options.
    """

    CONFIG = ProcessPoolConfig
    CONN_MANAGER = ZMQServer

    def __init__(
        self,
        name: str,
        size: Union[int, str] = 4,
        host: str = "127.0.0.1",
        port: int = 0,
        abort_signals: List[int] = None,
        worker_type: Type = ProcessWorker,
        worker_heartbeat: Union[int, float] = 5,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        super(ProcessPool, self).__init__(**options)

    def add(self, task: tasks.Task, uid: str) -> None:
        """
        Before adding Tasks to a ProcessPool, check that the Task target does
        not come from __main__.
        """
        if isinstance(task, tasks.Task) and task.module == "__main__":
            raise ValueError("Cannot add Tasks from __main__ to ProcessPool")
        super(ProcessPool, self).add(task, uid)
