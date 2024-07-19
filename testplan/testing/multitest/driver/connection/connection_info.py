from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional, Type

from .base import Direction, BaseConnectionInfo, BaseDriverConnection


@dataclass
class ConnectionInfo(BaseConnectionInfo):
    connectionType: Union[str, Type[BaseDriverConnection]]


class Protocol:
    TCP = "tcp"
    UDP = "udp"
    FILE = "file"
    default = [TCP, UDP, FILE]


@dataclass
class PortConnectionInfo(ConnectionInfo):
    """
    ConnectionInfo for port communication (e.g TCP/UDP) between drivers
    """

    local_port: Optional[int] = None  # port the driver is using
    local_host: Optional[str] = None  # host the driver is using

    @property
    def connection(self):
        # TODO: Add host info
        # identifier should be host:port
        return f"{self.protocol}://:{self.identifier}"


class PortDriverConnection(BaseDriverConnection):
    """
    Connection class for port communication (e.g TCP/UDP) between drivers
    """

    def __init__(self, driver_connection_info: PortConnectionInfo):
        super().__init__(driver_connection_info)

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: PortConnectionInfo
    ):
        if self.connection == driver_connection_info.connection:
            if (
                driver_connection_info.service.upper() != self.service
                and driver_connection_info.service.lower()
                not in Protocol.default
            ):
                self.service = driver_connection_info.service.upper()
            port = (
                str(driver_connection_info.local_port)
                if str(driver_connection_info.local_port)
                else "Unknown"
            )
            if (
                driver_connection_info.direction == Direction.listening
                and port not in self.drivers_listening[driver_name]
            ):
                self.drivers_listening[driver_name].append(port)
            elif (
                driver_connection_info.direction == Direction.connecting
                and port not in self.drivers_connecting[driver_name]
            ):
                self.drivers_connecting[driver_name].append(port)
            return True
        return False


@dataclass
class FileConnectionInfo(ConnectionInfo):
    """
    ConnectionInfo for file-based communication between drivers
    """

    @property
    def connection(self):
        return f"file://{self.identifier}"


class FileDriverConnection(BaseDriverConnection):
    """
    Connection class for file-based between drivers
    """

    def __init__(self, driver_connection_info: FileConnectionInfo):
        super().__init__(driver_connection_info)

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: FileConnectionInfo
    ):
        if self.connection == driver_connection_info.connection:
            if (
                driver_connection_info.direction == Direction.listening
                and "Read" not in self.drivers_listening[driver_name]
            ):
                self.drivers_listening[driver_name].append("Read")
            elif (
                driver_connection_info.direction == Direction.connecting
                and "Write" not in self.drivers_connecting[driver_name]
            ):
                self.drivers_connecting[driver_name].append("Write")
            return True
        return False
