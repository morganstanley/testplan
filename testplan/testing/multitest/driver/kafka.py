"""
Driver for Kafka server
"""
import os
import re

from schema import Or
from testplan.common.config import ConfigOption
from testplan.common.utils.path import (
    makeemptydirs,
    makedirs,
    instantiate,
)
from testplan.testing.multitest.driver import app

KAFKA_START = "/opt/kafka/bin/kafka-server-start.sh"


class KafkaStandaloneConfig(app.AppConfig):
    """"
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.kafka.KafkaStandalone` resource.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("cfg_template"): str,
            ConfigOption("port"): int,
        }


class KafkaStandalone(app.App):
    """
    Driver for starting a Kafka instance in standalone mode.

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
        self, name, cfg_template, binary=KAFKA_START, port=0, **options
    ):
        log_regexps = [
            re.compile(
                r".*Awaiting socket connections on\s*(?P<host>[^:]+):(?P<port>[0-9]+).*"
            ),
            re.compile(".*started.*"),
        ]
        super(KafkaStandalone, self).__init__(
            name=name,
            cfg_template=cfg_template,
            binary=binary,
            port=port,
            log_regexps=log_regexps,
            **options
        )

        self.zookeeper_connect = None
        self.log_path = None
        self.etc_path = None
        self.config = None
        self.port = port

    def pre_start(self):
        super(KafkaStandalone, self).pre_start()
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
    def cmd(self):
        return [self.cfg.binary, self.config]

    def started_check(self, timeout=None):
        """Driver started status condition check."""

        super(KafkaStandalone, self).started_check(timeout)
        self.port = int(self.extracts["port"])
