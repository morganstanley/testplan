"""
Module implementing RemoteService class. Based on RPyC package.
"""

import re
import shlex
import signal
import subprocess
import warnings
from typing import Optional

import rpyc
import rpyc.core.protocol
from rpyc import Connection
from schema import Use

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig
from testplan.common.remote.remote_resource import (
    RemoteResource,
    RemoteResourceConfig,
)
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import StdFiles
from testplan.common.utils.process import kill_process, subprocess_popen
from testplan.common.utils.timing import get_sleeper


class RemoteServiceConfig(ResourceConfig, RemoteResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.common.remote.remote_service.RemoteService` entity.
    """

    @classmethod
    def get_options(cls):
        """Resource specific config options."""
        return {
            "name": str,
            # NOTE: currently we have ``get_remote_rpyc_bin`` in ``RuntimeBuilder``,
            # NOTE: do we still need this config option here?
            ConfigOption("rpyc_bin", default=None): str,
            ConfigOption("rpyc_port", default=0): int,
            ConfigOption("stop_timeout", default=5): Use(float),
        }


class RemoteService(Resource, RemoteResource):
    """
    Spawns RPyC service on remote host via ssh and create RPyC connection for
    remote drivers.

    :param name: Name of the remote service.
    :param remote_host: Remote host name or IP address.
    :param rpyc_bin: Location of rpyc_classic.py script
    :param rpyc_port: Specific port for rpyc connection on the remote host. Defaults to 0
        which start the rpyc server on a random port.
    :param stop_timeout: Timeout of graceful shutdown (in seconds).

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` and
    :py:class:`~testplan.common.remote.remote_resource.RemoteResource` options
    """

    CONFIG = RemoteServiceConfig

    def __init__(
        self,
        name: str,
        remote_host: str,
        rpyc_bin: Optional[str] = None,
        rpyc_port: int = 0,
        stop_timeout: float = 5,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        options["async_start"] = False
        # ``sigint_timeout`` is deprecated
        if "sigint_timeout" in options:
            options["stop_timeout"] = options.pop("sigint_timeout")
            warnings.warn(
                "``sigint_timeout`` argument is deprecated, "
                "please use ``stop_timeout`` instead.",
                DeprecationWarning,
            )
        super(RemoteService, self).__init__(**options)

        self.proc: Optional[subprocess.Popen] = None
        # This mirrors the way default config is assigned, we only change
        # sync_request_timeout and pass it for the Connection object implicitly
        self.rpyc_config = rpyc.core.protocol.DEFAULT_CONFIG.copy()
        self.rpyc_config["sync_request_timeout"] = None
        self.rpyc_connection: Connection = None
        self.rpyc_port: Optional[int] = None
        self.rpyc_pid: Optional[int] = None
        self.std: StdFiles = None

    def __repr__(self) -> str:
        """
        String representation.
        """
        return f"{self.__class__.__name__}[{self.cfg.name}]"

    def uid(self) -> str:
        """
        Unique identifier.
        """
        return self.cfg.name

    def pre_start(self) -> None:
        """
        Before service start.
        """
        self.make_runpath_dirs()
        self.std = StdFiles(self.runpath)
        self._prepare_remote()

    def starting(self) -> None:
        """
        Starting the rpyc service on remote host.
        """
        rpyc_bin = (
            self.cfg.rpyc_bin
            or self._remote_runtime_builder.get_remote_rpyc_bin()
        )

        # TODO: refactor, use self._ssh_client instead
        # TODO: make use of paramiko Channel, add apis to our wrapper class
        cmd = self.cfg.ssh_cmd(
            self.ssh_cfg,
            shlex.join(
                [
                    self.remote_python_bin,
                    "-uB",
                    rpyc_bin,
                    "--host",
                    "0.0.0.0",
                    "-p",
                    str(self.cfg.rpyc_port),
                ]
            ),
        )

        self.proc = subprocess_popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=self.std.out,
            stderr=self.std.err,
            cwd=self.runpath,
        )

        self.logger.debug(
            "%s executes cmd: %s\n"
            "\tRunpath: %s\n"
            "\tPID: %s\n"
            "\tOut file: %s\n"
            "\tErr file: %s",
            self,
            " ".join(cmd),
            self.runpath,
            self.proc.pid,
            self.std.out_path,
            self.std.err_path,
        )

    def _wait_started(self, timeout: Optional[float] = None) -> None:
        """
        Waits for RPyC server start, changes status to STARTED.

        :param timeout: timeout in seconds
        :raises RuntimeError: if server startup fails
        """
        timeout: float = (
            timeout if timeout is not None else self.cfg.status_wait_timeout
        )
        sleeper = get_sleeper(
            interval=0.2,
            timeout=timeout,
            raise_timeout_with_msg=f"RPyC server start timeout, logfile = {self.std.err_path}",
        )
        while next(sleeper):
            done, extracts, _ = match_regexps_in_file(
                self.std.err_path,
                [re.compile(".*server started on .*:(?P<port>.*)")],
            )

            if done:
                self.rpyc_port = int(extracts["port"])
                self.logger.info(
                    "Remote RPyc server started on %s:%s",
                    self.cfg.remote_host,
                    self.rpyc_port,
                )
                super(RemoteService, self)._wait_started(timeout=timeout)
                return

            if self.proc and self.proc.poll() is not None:
                raise RuntimeError(
                    f"{self} process exited: {self.proc.returncode} (logfile = {self.std.err_path})"
                )

    def post_start(self) -> None:
        """
        After service is started.
        """
        self._config_server()

    def _config_server(self) -> None:
        """
        Configures rpyc connection.
        """
        self.rpyc_connection = rpyc.classic.factory.connect(
            host=self.cfg.remote_host,
            port=self.rpyc_port,
            service=rpyc.classic.SlaveService,
            config=self.rpyc_config,
            keepalive=True,
        )

        self.rpyc_pid = self.rpyc_connection.modules.os.getpid()

        for path in self._remote_sys_path():
            self.rpyc_connection.modules.sys.path.append(path)

        self.rpyc_connection.modules.os.chdir(self._working_dirs.remote)
        self.rpyc_connection.modules.os.environ["PWD"] = (
            self._working_dirs.remote
        )

        if "" not in self.rpyc_connection.modules.sys.path:
            self.rpyc_connection.modules.sys.path.insert(0, "")

    def pre_stop(self) -> None:
        """
        Before stopping the service.
        """
        self._fetch_results()

    def post_stop(self) -> None:
        """
        After stopping the service.
        """
        self._clean_remote()

    def stopping(self) -> None:
        """
        Stops remote rpyc process.
        """
        try:
            self.rpyc_connection.modules.os.kill(self.rpyc_pid, signal.SIGTERM)
        except EOFError:
            pass
        finally:
            # if remote rpyc server is shutdown successfully, ssh proc is also finished
            # otherwise we need to manual kill this orphaned ssh procc
            if self.proc:
                kill_process(self.proc, self.cfg.stop_timeout)
