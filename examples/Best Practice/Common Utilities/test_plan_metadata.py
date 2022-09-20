#!/usr/bin/env python
"""
Example demonstrating the usage of on-demand Driver metadata
extraction.
"""
import sys
from dataclasses import dataclass

from testplan_ms import test_plan
from testplan.common.utils import helper
from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.base import DriverMetadata
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


def before_start(env, result):
    """
    Extracts driver metadata before environment startup.
    """
    helper.extract_driver_metadata(env, result)


def after_start(env, result):
    """
    Accepts TCPClient connection on TCPServer side and extracts driver
    metadata after startup.
    """
    env.server.accept_connection()
    helper.extract_driver_metadata(env, result)


# NOTE: to add new fields using dataclass syntax requires the decoration
#            not just inheritance
@dataclass
class TCPServerMetadata(DriverMetadata):
    """
    DriverMetadata subclass to extend required fields with host and port.
    """

    host: str
    port: int


def metadata_extractor_server(driver: TCPServer) -> TCPServerMetadata:
    """
    TCPServer specific metadata extractor function.

    :param driver: TCPServer driver instance
    :return: driver name, driver class, host, and connecting port metadata
    """
    return TCPServerMetadata(
        name=driver.name,
        klass=driver.__class__.__name__,
        host=driver.cfg.host,
        port=driver.cfg.port,
    )


@dataclass
class TCPClientMetadata(DriverMetadata):
    """
    DriverMetadata subclass to extend required fields with host and port.
    """

    host: str
    port: int


def metadata_extractor_client(driver: TCPClient) -> TCPClientMetadata:
    """
    TCPClient specific metadata extractor function.

    :param driver: TCPClient driver instance
    :return: driver name, driver class, host, and connecting port metadata
    """
    return TCPClientMetadata(
        name=driver.name,
        klass=driver.__class__.__name__,
        host=driver.cfg.host,
        port=driver.cfg.port,
    )


@testsuite
class TCPSuite:
    @testcase
    def test_send_msg(self, env, result):
        """
        Simple testcase sending a message from client to server side at which it
        is received and the integrity is tested.
        """
        msg = "Hello Server!"
        msg_sent = env.client.send_text(msg)
        msg_received = env.server.receive_text(size=msg_sent)
        result.equal(msg_received, msg, "Message received on server side")


@test_plan(name="Example of Driver metadata extraction")
def main(plan):
    plan.add(
        MultiTest(
            name="Metadata extraction",
            suites=[TCPSuite()],
            environment=[
                TCPServer(
                    name="server", metadata_extractor=metadata_extractor_server
                ),
                TCPClient(
                    name="client",
                    host=context("server", "{{host}}"),
                    port=context("server", "{{port}}"),
                    metadata_extractor=metadata_extractor_client,
                ),
            ],
            before_start=before_start,
            after_start=after_start,
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
