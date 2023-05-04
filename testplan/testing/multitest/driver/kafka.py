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
from testplan.testing.multitest.driver import app

KAFKA_START = "/opt/kafka/bin/kafka-server-start.sh"


class KafkaStandaloneConfig(app.AppConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.kafka.KafkaStandalone` resource.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("cfg_template"): str,
            ConfigOption("host"): Or(str, None),
            ConfigOption("port"): int,
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
        host: Optional[str] = None,
        port: int = 0,
        **options
    ):
        stdout_regexps = [
            re.compile(
                r".*Awaiting socket connections on\s*(?P<host>[^:]+):(?P<port>[0-9]+).*"
            ),
            re.compile(".*started.*"),
        ]
        super(KafkaStandalone, self).__init__(
            name=name,
            cfg_template=cfg_template,
            binary=binary,
            host=host,
            port=port,
            stdout_regexps=stdout_regexps,
            **options
        )

        self.log_path = None
        self.etc_path = None
        self.config = None
        self._host = host
        self._port = port

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

    def pre_start(self):
        super(KafkaStandalone, self).pre_start()
        self._host = self._host or socket.getfqdn()
        self.log_path = os.path.join(self.runpath, "log")
        self.etc_path = os.path.join(self.runpath, "etc")
        for directory in (self.log_path, self.etc_path):
            if self.cfg.path_cleanup is False:
                makedirs(directory)
            else:
                makeemptydirs(directory)
        self.config = os.path.join(self.runpath, "etc", "server.properties")
        instantiate(self.cfg.cfg_template, self.context_input(), self.config)

    @property
    def cmd(self) -> List[str]:
        return [self.cfg.binary, self.config]

    def post_start(self):
        super().post_start()
        self._port = int(self.extracts["port"])
        self.logger.info("%s listening on %s:%s", self, self._host, self._port)
