from dataclasses import dataclass
from enum import Enum
from typing import List, Set
from collections import defaultdict


class Direction(Enum):
    CONNECTING = "connecting"
    LISTENING = "listening"


@dataclass
class BaseConnectionInfo:
    name: str  # name of the connection
    service: str  # e.g. HTTP, TCP, FIX
    protocol: str  # tcp, udp, file
    identifier: str
    direction: Direction

    @property
    def connection_rep(self):
        return f"{self.protocol}://{self.identifier}"

    def promote_to_connection(self):
        raise NotImplementedError


@dataclass
class BaseDriverConnectionGroup:
    """
    Base class to show connection between drivers.
    Each specific type (protocol) of connection should have its own subclass.

    Stores the drivers involved in the connection as well as the logic of whether to add a driver into the connection.

    in_drivers store incoming connections (e.g a server listening for connections), out_drivers store outgoing connections (e.g a client connecting to a server).
    """

    service: str
    connection_rep: str
    in_drivers: "defaultdict[Set]"
    out_drivers: "defaultdict[Set]"

    @classmethod
    def from_connection_info(cls, driver_connection_info: BaseConnectionInfo):
        conn = cls(
            service=driver_connection_info.service.upper(),
            connection_rep=driver_connection_info.connection_rep,
            in_drivers=defaultdict(set),
            out_drivers=defaultdict(set),
        )
        return conn

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: BaseConnectionInfo
    ):
        raise NotImplementedError

    def __str__(self):
        return (
            f"{self.__class__.__name__}[{self.service}-{self.connection_rep}]"
        )

    def should_include(self):
        return self.in_drivers and self.out_drivers


class BaseConnectionExtractor:
    def extract_connection(self, driver) -> List[BaseConnectionInfo]:
        raise NotImplementedError
