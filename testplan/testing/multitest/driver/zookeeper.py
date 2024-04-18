"""
Driver for Zookeeper server
"""
import os
import socket
from typing import Optional, Dict

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.path import (
    StdFiles,
    instantiate,
    makedirs,
    makeemptydirs,
)
from testplan.common.utils.process import execute_cmd
from testplan.testing.multitest.driver.base import Driver, DriverConfig

ZK_SERVER = "/usr/share/zookeeper/bin/zkServer.sh"


class ZookeeperStandaloneConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.zookeeper.ZookeeperStandalone` resource.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("cfg_template"): str,
            ConfigOption("binary"): str,
            ConfigOption("host"): Or(None, str),
            ConfigOption("port"): int,
            ConfigOption("env", default=None): Or(None, dict),
        }


class ZookeeperStandalone(Driver):
    """
    Driver for starting a Zookeeper instance in standalone mode.

    {emphasized_members_docs}

    :param template: Zookeeper config file template.
    :type template: ``str``
    :param binary: zkServer.sh file path.
    :type binary: ``str``
    :param port: Zookeeper listen port. Zookeeper doesn't support random port
    :type port: ``int``
    :param env: Environmental variables to be made available to Zookeeper process.
    :type env: ``dict``
    """

    CONFIG = ZookeeperStandaloneConfig

    def __init__(
        self,
        name: str,
        cfg_template: str,
        binary: str = ZK_SERVER,
        host: Optional[str] = None,
        port: int = 2181,
        env: Optional[dict] = None,
        **options,
    ):
        super(ZookeeperStandalone, self).__init__(
            name=name,
            cfg_template=cfg_template,
            binary=binary,
            host=host,
            port=port,
            env=env,
            **options,
        )
        self._host = host
        self._port = port
        self._env = None
        self.config = None
        self.zkdata_path = None
        self.zklog_path = None
        self.etc_path = None
        self.pid_file = None
        self.std = None

    @emphasized
    @property
    def host(self) -> str:
        """Host to bind to."""
        if self._host is None:
            raise RuntimeError(
                "Host not resolved yet, shouldn't be accessed now."
            )
        return self._host

    @emphasized
    @property
    def port(self) -> int:
        """Port to listen on."""
        return self._port

    @emphasized
    @property
    def env(self) -> Dict[str, str]:
        """Environment variables."""
        if self._env is not None:
            return self._env
        self._env = self.cfg.env.copy() if self.cfg.env else {}
        return self._env

    @emphasized
    @property
    def connection_str(self) -> str:
        """Connection string."""
        if self._host is None:
            raise RuntimeError(
                "Host not resolved yet, shouldn't be accessed now."
            )
        return "{}:{}".format(self._host, self._port)

    def pre_start(self):
        """
        Create mandatory directories and install files from given templates
        using the drivers context before starting zookeeper.
        """
        super(ZookeeperStandalone, self).pre_start()
        self.zkdata_path = os.path.join(self.runpath, "zkdata")
        self.zklog_path = os.path.join(self.runpath, "zklog")
        self.etc_path = os.path.join(self.runpath, "etc")
        self.env["ZOO_LOG_DIR"] = self.zklog_path
        for directory in (self.zkdata_path, self.zklog_path, self.etc_path):
            if self.cfg.path_cleanup is False:
                makedirs(directory)
            else:
                makeemptydirs(directory)
        self.config = os.path.join(self.runpath, "etc", "zookeeper.cfg")
        self._host = self._host or socket.getfqdn()
        if self._port == 0:
            raise RuntimeError("Zookeeper doesn't support random port")
        instantiate(self.cfg.cfg_template, self.context_input(), self.config)

    def starting(self):
        """Starts the Zookeeper instance."""
        super(ZookeeperStandalone, self).starting()
        start_cmd = [self.cfg.binary, "start", self.config]
        self.std = StdFiles(self.runpath)

        execute_cmd(
            start_cmd,
            label=self.uid(),
            check=True,
            stdout=self.std.out,
            stderr=self.std.err,
            logger=self.logger,
            env=self.env,
        )

    def post_start(self):
        super().post_start()
        self.logger.info("%s listening on %s:%s", self, self.host, self.port)

    def stopping(self):
        """Stops the Zookeeper instance."""
        stop_cmd = [self.cfg.binary, "stop", self.config]
        try:
            execute_cmd(
                stop_cmd,
                label=self.uid(),
                check=True,
                stdout=self.std.out,
                stderr=self.std.err,
                logger=self.logger,
                env=self.env,
            )
        finally:
            self.std.close()
