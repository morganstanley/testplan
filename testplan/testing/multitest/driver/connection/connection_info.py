from dataclasses import dataclass
from typing import Optional

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
        return PortDriverConnection.from_connection_info(self)


class PortDriverConnection(BaseDriverConnection):
    """
    Connection class for port communication (e.g TCP/UDP) between drivers
    """

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: PortConnectionInfo
    ):
        if self.connection_rep == driver_connection_info.connection_rep:
            if (
                driver_connection_info.service.upper() != self.service
                and driver_connection_info.service.lower()
                not in Protocol.default
            ):
                if self.service.lower() not in Protocol.default:
                    # if the service has been updated already, raise an error
                    msg = f"Driver connection service do not match. {driver_connection_info.service.upper()} != {self.service}"
                    raise ValueError(msg)
                else:
                    self.service = driver_connection_info.service.upper()

            port = (
                str(driver_connection_info.local_port)
                if driver_connection_info.local_port is not None
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
        return FileDriverConnection.from_connection_info(self)


class FileDriverConnection(BaseDriverConnection):
    """
    Connection class for file-based communication between drivers
    """

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
