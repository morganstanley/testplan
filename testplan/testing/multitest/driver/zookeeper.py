"""
Driver for Zookeeper server
"""

import os
import socket
from typing import Any, Dict, Optional

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

from .base import (
    Driver,
    DriverConfig,
)
from .connection import (
    Direction,
    Protocol,
    ConnectionExtractor,
)

ZK_SERVER = "/usr/share/zookeeper/bin/zkServer.sh"


class ZookeeperStandaloneConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.zookeeper.ZookeeperStandalone` resource.
    """

    @classmethod
    def get_options(cls) -> Dict[Any, Any]:
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
    EXTRACTORS = [ConnectionExtractor(Protocol.TCP, Direction.LISTENING)]

    def __init__(
        self,
        name: str,
        cfg_template: str,
        binary: str = ZK_SERVER,
        host: Optional[str] = None,
        port: int = 2181,
        env: Optional[dict] = None,
        **options: Any,
    ) -> None:
        super(ZookeeperStandalone, self).__init__(
            name=name,
            cfg_template=cfg_template,
            binary=binary,
            host=host,
            port=port,
            env=env,
            **options,
        )
        self._host: Optional[str] = host
        self._port: int = port
        self._env: Optional[Dict[str, str]] = None
        self.config: Optional[str] = None
        self.zkdata_path: Optional[str] = None
        self.zklog_path: Optional[str] = None
        self.etc_path: Optional[str] = None
        self.pid_file: Optional[str] = None
        self.std: Optional[StdFiles] = None

    @emphasized  # type: ignore[prop-decorator]
    @property
    def host(self) -> str:
        """Host to bind to."""
        if self._host is None:
            raise RuntimeError(
                "Host not resolved yet, shouldn't be accessed now."
            )
        return self._host

    @emphasized  # type: ignore[prop-decorator]
    @property
    def port(self) -> int:
        """Port to listen on."""
        return self._port

    @emphasized  # type: ignore[prop-decorator]
    @property
    def env(self) -> Dict[str, str]:
        """Environment variables."""
        if self._env is not None:
            return self._env
        self._env = self.cfg.env.copy() if self.cfg.env else {}
        return self._env

    @emphasized  # type: ignore[prop-decorator]
    @property
    def connection_str(self) -> str:
        """Connection string."""
        if self._host is None:
            raise RuntimeError(
                "Host not resolved yet, shouldn't be accessed now."
            )
        return "{}:{}".format(self._host, self._port)

    @property
    def connection_identifier(self) -> int:
        return self.port

    @property
    def local_port(self) -> int:
        return self.port

    @property
    def local_host(self) -> Optional[str]:
        return self.host if self._host else None

    def pre_start(self) -> None:
        """
        Create mandatory directories and install files from given templates
        using the drivers context before starting zookeeper.
        """
        super(ZookeeperStandalone, self).pre_start()
        self.zkdata_path = os.path.join(self.runpath, "zkdata")  # type: ignore[arg-type]
        self.zklog_path = os.path.join(self.runpath, "zklog")  # type: ignore[arg-type]
        self.etc_path = os.path.join(self.runpath, "etc")  # type: ignore[arg-type]
        self.env["ZOO_LOG_DIR"] = self.zklog_path
        for directory in (self.zkdata_path, self.zklog_path, self.etc_path):
            if self.cfg.path_cleanup is False:
                makedirs(directory)
            else:
                makeemptydirs(directory)
        self.config = os.path.join(self.runpath, "etc", "zookeeper.cfg")  # type: ignore[arg-type]
        self._host = self._host or socket.getfqdn()
        if self._port == 0:
            raise RuntimeError("Zookeeper doesn't support random port")
        instantiate(self.cfg.cfg_template, self.context_input(), self.config)

    def starting(self) -> None:
        """Starts the Zookeeper instance."""
        super(ZookeeperStandalone, self).starting()
        start_cmd = [self.cfg.binary, "start", self.config]
        if self.runpath is None:
            raise RuntimeError("self.runpath must not be None")
        self.std = StdFiles(self.runpath)

        execute_cmd(
            start_cmd,
            label=self.uid(),
            check=True,
            stdout=self.std.out,  # type: ignore[arg-type]
            stderr=self.std.err,  # type: ignore[arg-type]
            logger=self.logger,
            env=self.env,
        )

    def post_start(self) -> None:
        super().post_start()
        self.logger.info("%s listening on %s:%s", self, self.host, self.port)

    def stopping(self) -> None:
        """Stops the Zookeeper instance."""
        stop_cmd = [self.cfg.binary, "stop", self.config]
        try:
            if self.std is None:
                raise RuntimeError("self.std must not be None")
            execute_cmd(
                stop_cmd,
                label=self.uid(),
                check=True,
                stdout=self.std.out,  # type: ignore[arg-type]
                stderr=self.std.err,  # type: ignore[arg-type]
                logger=self.logger,
                env=self.env,
            )
        finally:
            if self.std is not None:
                self.std.close()
        super().stopping()
