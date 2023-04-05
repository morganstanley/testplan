"""
Module implementing RemoteService class. Based on RPyC package.
"""
import os
import re
import signal
import subprocess
from typing import Optional

import rpyc
from rpyc import Connection

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig
from testplan.common.remote.remote_resource import (
    RemoteResourceConfig,
    RemoteResource,
)
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import StdFiles
from testplan.common.utils.process import subprocess_popen, kill_process
from testplan.common.utils.timing import get_sleeper

RPYC_BIN = os.path.join(
    os.path.dirname(rpyc.__file__),
    os.pardir,
    os.pardir,
    "bin",
    "rpyc_classic.py",
)


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
            ConfigOption("rpyc_bin", default=RPYC_BIN): str,
            ConfigOption("rpyc_port", default=0): int,
            ConfigOption("sigint_timeout", default=5): int,
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
    :param sigint_timeout: number of seconds to wait between ``SIGINT`` and ``SIGKILL``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` and
    :py:class:`~testplan.common.remote.remote_resource.RemoteResource` options
    """

    CONFIG = RemoteServiceConfig

    def __init__(
        self,
        name: str,
        remote_host: str,
        rpyc_bin: str = RPYC_BIN,
        rpyc_port: str = 0,
        sigint_timeout: int = 5,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        options["async_start"] = False
        super(RemoteService, self).__init__(**options)

        self.proc: Optional[subprocess.Popen] = None
        # This mirrors the way default config is assigned, we only change
        # snyc_request_timeout and pass it for the Connection object implicitly
        self.rpyc_config = rpyc.core.protocol.DEFAULT_CONFIG.copy()
        self.rpyc_config["snyc_request_timeout"] = None
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
        cmd = self.cfg.ssh_cmd(
            self.ssh_cfg,
            " ".join(
                [
                    self.python_binary,
                    "-uB",
                    self.cfg.rpyc_bin,
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

    def _wait_started(self, timeout: float = None) -> None:
        """
        Waits for RPyC server start, changes status to STARTED.

        :param timeout: timeout in seconds
        :raises: RuntimeError if server startup fails
        """
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
        self.rpyc_connection.modules.os.environ[
            "PWD"
        ] = self._working_dirs.remote

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
        remote_pid = self.rpyc_connection.modules.os.getpid()
        try:
            self.rpyc_connection.modules.os.kill(remote_pid, signal.SIGTERM)
        except EOFError:
            pass

        # actually if remote rpyc server is shutdown, ssh proc is also finished
        # but calling kill_process just in case
        if self.proc:
            kill_process(self.proc, self.cfg.sigint_timeout)
            self.proc.wait()

        self.status.change(self.STATUS.STOPPED)
