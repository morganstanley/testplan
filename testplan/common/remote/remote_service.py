import os
import re
import signal
import subprocess

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig
from testplan.common.remote.remote_resource import (
    RemoteResourceConfig,
    RemoteResource,
)
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import StdFiles
from testplan.common.utils.process import (
    subprocess_popen,
    kill_process,
)
from testplan.common.utils.timing import get_sleeper

import rpyc

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
        }


class RemoteService(Resource, RemoteResource):
    """
    Spawns RPyC service on remote host via ssh and create RPyC connection for
    remote drivers.

    :param name: Name of the remote service.
    :type name: ``str``
    :param remote_host: Remote host name or IP address.
    :type remote_host: ``str``
    :param rpyc_bin: Location of rpyc_classic.py script
    :type rpyc_bin: ``str``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` and
    :py:class:`~testplan.common.remote.remote_resource.RemoteResource` options
    """

    CONFIG = RemoteServiceConfig

    def __init__(self, name, remote_host, rpyc_bin=RPYC_BIN, **options):

        options.update(self.filter_locals(locals()))
        options["async_start"] = False
        super(RemoteService, self).__init__(**options)

        self.proc = None
        self.rpyc_connection = None
        self.rpyc_port = None
        self.rpyc_pid = None
        self.std = None

    def __repr__(self):
        """String representation."""

        return f"{self.__class__.__name__} [{self.cfg.name}]"

    def uid(self):
        return self.cfg.name

    def pre_start(self):
        """Before service start"""
        self.make_runpath_dirs()
        self.std = StdFiles(self.runpath)
        self._prepare_remote()

    def starting(self):
        """Starting the rpyc service on remote host"""

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
                    "0",
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
            f"{self} executes cmd: {cmd}\n"
            f"\tRunpath: {self.runpath}\n"
            f"\tPid: {self.proc.pid}\n"
            f"\tOut file: {self.std.out_path}\n"
            f"\tErr file: {self.std.err_path}\n"
        )

    def _wait_started(self, timeout=None):

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
                self.status.change(self.STATUS.STARTED)
                return

            if self.proc and self.proc.poll() is not None:
                raise RuntimeError(
                    f"{self} process exited: {self.proc.returncode} (logfile = {self.std.err_path})"
                )

    def post_start(self):
        """After service is started"""
        self._config_server()

    def _config_server(self):

        self.rpyc_connection = rpyc.classic.connect(
            self.cfg.remote_host, self.rpyc_port, keepalive=True
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

    def pre_stop(self):
        """Before stopping the service"""
        self._fetch_results()

    def post_stop(self):
        self._clean_remote()

    def stopping(self):
        """Stop remote rpyc process"""
        remote_pid = self.rpyc_connection.modules.os.getpid()
        try:
            self.rpyc_connection.modules.os.kill(remote_pid, signal.SIGTERM)
        except EOFError:
            pass

        # actually if remote rpyc server is shutdown, ssh proc is also finished
        # but calling kill_process just in case
        if self.proc:
            kill_process(self.proc)
            self.proc.wait()

        self.status.change(self.STATUS.STOPPED)
