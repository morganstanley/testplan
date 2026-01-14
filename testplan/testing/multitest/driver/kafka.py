"""
Driver for Kafka server
"""

import os
import re
import socket
from typing import List, Optional

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.path import instantiate, makedirs, makeemptydirs
from testplan.common.utils.process import execute_cmd
from testplan.testing.multitest.driver import app


KAFKA_BIN_PATH = "/opt/kafka/bin"
KAFKA_START = f"{KAFKA_BIN_PATH}/kafka-server-start.sh"
KAFKA_STORAGE = f"{KAFKA_BIN_PATH}/kafka-storage.sh"


class KafkaStandaloneConfig(app.AppConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.kafka.KafkaStandalone` resource.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("cfg_template"): str,
            ConfigOption("host"): str,
            ConfigOption("port"): int,
            ConfigOption("node_id"): int,
            ConfigOption("controller_port"): int,
            ConfigOption("controller_quorum_voters"): Or(str, None),
            ConfigOption("kafka_storage"): str,
            ConfigOption("cluster_id"): Or(str, None),
        }


class KafkaStandalone(app.App):
    """
    Driver for starting a Kafka instance in standalone mode.

    {emphasized_members_docs}

    :param cfg_template: Kafka config file template.
    :type cfg_template: ``str``
    :param binary: kafka-server-start.sh file path.
    :type binary: ``str``
    :param port: Kafka listen port.
    :type port: ``int``
    :param env: Environmental variables to be made available to Zookeeper process.
    :type env: ``dict``
    """

    CONFIG = KafkaStandaloneConfig

    def __init__(
        self,
        name: str,
        cfg_template: str,
        binary: str = KAFKA_START,
        host: str = "localhost",
        port: int = 0,
        node_id: int = 1,
        controller_port: int = 0,
        controller_quorum_voters: Optional[str] = None,
        kafka_storage: str = KAFKA_STORAGE,
        cluster_id: str = None,
        **options,
    ):
        stdout_regexps = [
            re.compile(
                rf".*Awaiting socket connections on\s*(?P<host>[^:]+):(?P<port>(?!{controller_port}\b)[0-9]+).*"
            ),
            re.compile(".*started.*"),
        ]
        install_files = options.pop("install_files", [])
        install_files.append(cfg_template)
        super(KafkaStandalone, self).__init__(
            name=name,
            cfg_template=cfg_template,
            binary=binary,
            host=host,
            port=port,
            node_id=node_id,
            controller_port=controller_port,
            stdout_regexps=stdout_regexps,
            controller_quorum_voters=controller_quorum_voters,
            kafka_storage=kafka_storage,
            install_files=install_files,
            cluster_id=cluster_id,
            **options,
        )

        self._host = host
        self._port = port
        self._controller_port = controller_port
        self._controller_quorum_voters = controller_quorum_voters

    @emphasized
    @property
    def host(self) -> str:
        return self._host

    @emphasized
    @property
    def port(self) -> int:
        """Port to listen on."""
        return self._port

    @emphasized
    @property
    def node_id(self) -> int:
        """Node ID."""
        return self.cfg.node_id

    @emphasized
    @property
    def controller_port(self) -> int:
        """Controller port."""
        return self._controller_port

    @emphasized
    @property
    def controller_quorum_voters(self) -> str:
        if not self._controller_quorum_voters:
            self._controller_quorum_voters = (
                f"{self.cfg.node_id}@{self.host}:{self.controller_port}"
            )
        return self._controller_quorum_voters

    @property
    def log_path(self) -> str:
        return os.path.join(self.runpath, "etc")

    @property
    def etc_path(self) -> str:
        """
        Decorated etc path property.
        """
        return self.etcpath

    @property
    def config_path(self) -> str:
        return os.path.join(
            self.etcpath, os.path.basename(self.cfg.cfg_template)
        )

    def pre_start(self):
        super(KafkaStandalone, self).pre_start()
        makedirs(self.log_path)
        with open(self.config_path) as config_file:
            config_data = config_file.read()
            if "controller.quorum.voter" in config_data:
                self.format_meta()

    def format_meta(self):
        cmd = [
            self.cfg.kafka_storage,
            "format",
            "-t",
            self.name,
            "-c",
            self.config_path,
            "--ignore-formatted",
        ]
        if self.cfg.cluster_id:
            cmd.extend(["--cluster-id", self.cfg.cluster_id])
        execute_cmd(cmd, env=self.env, label=self.uid(), logger=self.logger)

    @property
    def cmd(self) -> List[str]:
        return [self.cfg.binary, self.config_path]

    def post_start(self):
        super().post_start()
        self._port = int(self.extracts["port"])
        self.logger.info("%s listening on %s:%s", self, self._host, self._port)
