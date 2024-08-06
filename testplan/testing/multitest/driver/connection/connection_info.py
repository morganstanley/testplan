from dataclasses import dataclass
import re
from typing import List, Optional

from testplan.testing.multitest.driver.connection.base import (
    Direction,
    BaseConnectionInfo,
    BaseDriverConnectionGroup,
)


class Protocol:
    TCP = "tcp"
    UDP = "udp"
    FILE = "file"
    default = [TCP, UDP, FILE]


@dataclass
class PortConnectionInfo(BaseConnectionInfo):
    """
    ConnectionInfo for port communication (e.g TCP/UDP) between drivers.
    """

    port: Optional[int] = None  # port the driver is using
    host: Optional[str] = None  # host the driver is using

    def promote_to_connection(self):
        return PortDriverConnectionGroup.from_connection_info(self)


class PortDriverConnectionGroup(BaseDriverConnectionGroup):
    """
    ConnectionGroup for port communication (e.g TCP/UDP) between drivers.

    Stores the drivers involved in the connection as well as the logic of whether to add a driver into the connection.
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
                str(driver_connection_info.port)
                if driver_connection_info.port is not None
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
    ConnectionInfo for file-based communication between drivers.
    """

    def promote_to_connection(self):
        return FileDriverConnectionGroup.from_connection_info(self)


class FileDriverConnectionGroup(BaseDriverConnectionGroup):
    """
    ConnectionGroup for file-based communication between drivers.

    Stores the drivers involved in the connection as well as the logic of whether to add a driver into the connection.
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


class DriverConnectionGraph:
    def __init__(self, drivers):
        self.drivers = drivers
        self.connections: List[BaseDriverConnectionGroup] = []
        self._nodes = []
        self._edges = []

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    def add_connection(self, driver_name: str, conn_info: BaseConnectionInfo):
        added = False
        for existing_connection in self.connections:
            added = existing_connection.add_driver_if_in_connection(
                driver_name, conn_info
            )
            if added:
                break
        if not added:
            new_connection = conn_info.promote_to_connection()
            new_connection.add_driver_if_in_connection(driver_name, conn_info)
            self.connections.append(new_connection)

    def set_nodes_and_edges(self):
        drivers = set([str(driver) for driver in self.drivers])
        unconnected_drivers = set(drivers)
        for connection in self.connections:
            if connection.should_include():
                for (
                    listening_driver,
                    listening_driver_identifier,
                ) in connection.drivers_listening.items():
                    # in case custom drivers are added in connections
                    drivers.add(listening_driver)
                    for (
                        connecting_driver,
                        connecting_driver_identifier,
                    ) in connection.drivers_connecting.items():
                        drivers.add(connecting_driver)
                        if listening_driver == connecting_driver:
                            continue
                        unconnected_drivers.discard(listening_driver)
                        unconnected_drivers.discard(connecting_driver)
                        self._edges.append(
                            {
                                "id": f"{connection.connection_rep}: {connecting_driver} -> {listening_driver}",
                                "source": connecting_driver,
                                "target": listening_driver,
                                "startLabel": ",".join(
                                    connecting_driver_identifier
                                ),
                                "label": connection.connection_rep,
                                "endLabel": ",".join(
                                    listening_driver_identifier
                                ),
                            }
                        )
        self._nodes = [
            {
                "id": driver,
                "data": {
                    "label": re.sub(r"(\w+)(\[\w+\])", r"\1\n\2", driver)
                },
                "style": (
                    {"border": "1px solid #FF0000"}
                    if driver in unconnected_drivers
                    else {}
                ),
            }
            for driver in drivers
        ]
