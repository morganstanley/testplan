from dataclasses import dataclass
from enum import Enum
from typing import List
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
class BaseDriverConnection:
    """
    Base class to show connection between drivers.
    Each specific type (protocol) of connection should have its own subclass.
    """

    service: str
    connection_rep: str
    drivers_listening: "defaultdict[List]"
    drivers_connecting: "defaultdict[List]"

    @classmethod
    def from_connection_info(cls, driver_connection_info: BaseConnectionInfo):
        conn = cls(
            service=driver_connection_info.service.upper(),
            connection_rep=driver_connection_info.connection_rep,
            drivers_listening=defaultdict(list),
            drivers_connecting=defaultdict(list),
        )
        return conn

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: BaseConnectionInfo
    ):
        raise NotImplementedError

    def __str__(self):
        return f"{self.service}-{self.connection_rep}"

    def should_include(self):
        return self.drivers_connecting and self.drivers_listening


class BaseConnectionExtractor:
    def extract_connection(self, driver) -> List[BaseConnectionInfo]:
        raise NotImplementedError
