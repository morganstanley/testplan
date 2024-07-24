from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional, Type

from testplan.testing.multitest.driver.connection.base import (
    Direction,
    BaseConnectionInfo,
    BaseDriverConnection,
)


class Protocol:
    TCP = "tcp"
    UDP = "udp"
    FILE = "file"
    default = [TCP, UDP, FILE]


@dataclass
class PortConnectionInfo(BaseConnectionInfo):
    """
    ConnectionInfo for port communication (e.g TCP/UDP) between drivers
    """

    local_port: Optional[int] = None  # port the driver is using
    local_host: Optional[str] = None  # host the driver is using

    @property
    def connection_rep(self):
        # TODO: Add host info
        # identifier should be host:port
        return f"{self.protocol}://:{self.identifier}"

    def promote_to_connection(self):
        conn = PortDriverConnection.from_connection_info(self)
        conn.add_driver_if_in_connection(self)
        return conn


class PortDriverConnection(BaseDriverConnection):
    """
    Connection class for port communication (e.g TCP/UDP) between drivers
    """

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: PortConnectionInfo
    ):
        if self.connection_rep == driver_connection_info.connection_rep:
            if driver_connection_info.service.upper() != self.service:
                if (
                    driver_connection_info.service.lower()
                    not in Protocol.default
                ):
                    self.service = driver_connection_info.service.upper()
                else:
                    msg = f"Driver connection service do not match. {driver_connection_info.service.upper()} != {self.service}"
                    raise ValueError(msg)
            port = (
                str(driver_connection_info.local_port)
                if str(driver_connection_info.local_port)
                else "Unknown"
            )
            if (
                driver_connection_info.direction == Direction.LISTENING
                and port not in self.drivers_listening[driver_name]
            ):
                self.drivers_listening[driver_name].append(port)
            elif (
                driver_connection_info.direction == Direction.CONNECTING
                and port not in self.drivers_connecting[driver_name]
            ):
                self.drivers_connecting[driver_name].append(port)
            return True
        return False


@dataclass
class FileConnectionInfo(BaseConnectionInfo):
    """
    ConnectionInfo for file-based communication between drivers
    """

    @property
    def connection_rep(self):
        return f"file://{self.identifier}"

    def promote_to_connection(self):
        conn = FileDriverConnection.from_connection_info(self)
        conn.add_driver_if_in_connection(self)
        return conn


class FileDriverConnection(BaseDriverConnection):
    """
    Connection class for file-based between drivers
    """

    def __init__(self, driver_connection_info: FileConnectionInfo):
        super().__init__(driver_connection_info)

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: FileConnectionInfo
    ):
        if self.connection_rep == driver_connection_info.connection_rep:
            if (
                driver_connection_info.direction == Direction.LISTENING
                and "Read" not in self.drivers_listening[driver_name]
            ):
                self.drivers_listening[driver_name].append("Read")
            elif (
                driver_connection_info.direction == Direction.CONNECTING
                and "Write" not in self.drivers_connecting[driver_name]
            ):
                self.drivers_connecting[driver_name].append("Write")
            return True
        return False
