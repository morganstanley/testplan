"""
Module implementing RemoteService class. Based on RPyC package.
"""

import os
import re
import shlex
import shutil
import signal
import socket
import ssl
import subprocess
import tempfile
import warnings
from typing import Any, Dict, Optional

import rpyc
import rpyc.core.protocol
import rpyc.core.stream
import rpyc.utils.factory
from rpyc import Connection
from schema import Use

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig
from testplan.common.remote import gen_cert
from testplan.common.remote.remote_resource import (
    RemoteResource,
    RemoteResourceConfig,
)
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import StdFiles
from testplan.common.utils.process import kill_process, subprocess_popen
from testplan.common.utils.remote import rm_cmd
from testplan.common.utils.timing import get_sleeper


class RemoteServiceConfig(ResourceConfig, RemoteResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.common.remote.remote_service.RemoteService` entity.
    """

    @classmethod
    def get_options(cls) -> Dict[Any, Any]:
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
    remote drivers. The connection uses mutual TLS with throwaway self-signed
    certs, made for each run and deleted after the connection is made.

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
        **options: Any,
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

        self.proc: Optional[subprocess.Popen[bytes]] = None
        # This mirrors the way default config is assigned, we only change
        # sync_request_timeout and pass it for the Connection object implicitly
        self.rpyc_config = rpyc.core.protocol.DEFAULT_CONFIG.copy()
        self.rpyc_config["sync_request_timeout"] = None
        self.rpyc_connection: Optional[Connection] = None
        self.rpyc_port: Optional[int] = None
        self.rpyc_pid: Optional[int] = None
        self.std: Optional[StdFiles] = None
        self._tls_local_dir: Optional[str] = None
        self._tls_remote_dir: Optional[str] = None

    def __repr__(self) -> str:
        """
        String representation.
        """
        return f"{self.__class__.__name__}[{self.cfg.name}]"

    def uid(self) -> str:
        """
        Unique identifier.
        """
        return str(self.cfg.name)

    def pre_start(self) -> None:
        """
        Before service start.
        """
        self.make_runpath_dirs()
        self.std = StdFiles(self.runpath)
        self._prepare_remote()

    def _setup_tls(self) -> None:
        """
        Make both cert pairs locally, copy the needed files over.
        """
        local_dir = tempfile.mkdtemp(prefix="testplan_tls_")
        remote_dir = "/".join([self._remote_resource_runpath, "tls"])
        self._tls_local_dir = local_dir
        self._tls_remote_dir = remote_dir

        client_dir = os.path.join(local_dir, "client")
        server_dir = os.path.join(local_dir, "server")
        gen_cert.generate(client_dir, "testplan-client")
        gen_cert.generate(server_dir, "testplan-server")

        self._ssh_client.exec_command(
            ["/bin/mkdir", "-p", "-m", "700", remote_dir],
            label="create remote tls dir",
        )
        sftp = self._ssh_client.sftp_client
        key, cert = gen_cert.KEY_NAME, gen_cert.CERT_NAME
        for local_path, name, mode in (
            (os.path.join(server_dir, key), "server_key.pem", 0o600),
            (os.path.join(server_dir, cert), "server.pem", 0o644),
            (os.path.join(client_dir, cert), "client.pem", 0o644),
        ):
            remote_path = f"{remote_dir}/{name}"
            sftp.put(local_path, remote_path)
            sftp.chmod(remote_path, mode)

    def _discard_tls(self) -> None:
        """
        Delete all key and cert files, local and remote.
        """
        if self._tls_local_dir:
            shutil.rmtree(self._tls_local_dir, ignore_errors=True)
            self._tls_local_dir = None
        if self._tls_remote_dir:
            try:
                self._ssh_client.exec_command(
                    rm_cmd(self._tls_remote_dir),
                    label="delete remote tls dir",
                    check=False,
                )
            except Exception:
                self.logger.warning(
                    "%s: cannot delete remote tls dir %s",
                    self,
                    self._tls_remote_dir,
                )
            self._tls_remote_dir = None

    def _connect_tls(self) -> Connection:
        """
        Connect to the server, both sides check the peer cert.
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # trust only the pinned server cert, no hostname in it
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(
            cafile=os.path.join(
                self._tls_local_dir, "server", gen_cert.CERT_NAME
            )
        )
        context.load_cert_chain(
            certfile=os.path.join(
                self._tls_local_dir, "client", gen_cert.CERT_NAME
            ),
            keyfile=os.path.join(
                self._tls_local_dir, "client", gen_cert.KEY_NAME
            ),
        )

        sock = socket.create_connection(
            (self.cfg.remote_host, self.rpyc_port),
            timeout=self.cfg.status_wait_timeout,
        )
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            tls_sock = context.wrap_socket(sock)
        except BaseException:
            sock.close()
            raise
        tls_sock.settimeout(None)

        return rpyc.utils.factory.connect_stream(
            rpyc.core.stream.SocketStream(tls_sock),
            service=rpyc.classic.SlaveService,
            config=self.rpyc_config,
        )

    def starting(self) -> None:
        """
        Starting the rpyc service on remote host.
        """
        rpyc_bin = (
            self.cfg.rpyc_bin
            or self._remote_runtime_builder.get_remote_rpyc_bin()
        )
        self._setup_tls()
        remote_dir = self._tls_remote_dir

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
                    "--ssl-keyfile",
                    f"{remote_dir}/server_key.pem",
                    "--ssl-certfile",
                    f"{remote_dir}/server.pem",
                    "--ssl-cafile",
                    f"{remote_dir}/client.pem",
                ]
            ),
        )

        self.proc = subprocess_popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=self.std.out,  # type: ignore[arg-type, union-attr]
            stderr=self.std.err,  # type: ignore[arg-type, union-attr]
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
            self.std.out_path,  # type: ignore[union-attr]
            self.std.err_path,  # type: ignore[union-attr]
        )

    def _wait_started(self, timeout: Optional[float] = None) -> None:
        """
        Waits for RPyC server start, changes status to STARTED.

        :param timeout: timeout in seconds
        :raises RuntimeError: if server startup fails
        """
        effective_timeout: float = (
            timeout if timeout is not None else self.cfg.status_wait_timeout
        )
        sleeper = get_sleeper(
            interval=0.2,
            timeout=effective_timeout,
            raise_timeout_with_msg=f"RPyC server start timeout, logfile = {self.std.err_path}",  # type: ignore[union-attr]
        )
        while next(sleeper):
            done, extracts, _ = match_regexps_in_file(
                self.std.err_path,  # type: ignore[union-attr]
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
                    f"{self} process exited: {self.proc.returncode} (logfile = {self.std.err_path})"  # type: ignore[union-attr]
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
        try:
            self.rpyc_connection = self._connect_tls()
        finally:
            # server has read the files by now
            self._discard_tls()

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
            if self.rpyc_connection is None:
                raise RuntimeError("rpyc connection is not established")
            self.rpyc_connection.modules.os.kill(self.rpyc_pid, signal.SIGTERM)
        except EOFError:
            pass
        finally:
            self._discard_tls()
            # if remote rpyc server is shutdown successfully, ssh proc is also finished
            # otherwise we need to manual kill this orphaned ssh procc
            if self.proc:
                kill_process(self.proc, self.cfg.stop_timeout)
