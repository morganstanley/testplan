from dataclasses import dataclass
from enum import Enum
from typing import Union
from collections import defaultdict

from testplan.common.utils.context import ContextValue


class Direction(Enum):
    CONNECTING = "connecting"
    LISTENING = "listening"


@dataclass
class BaseConnectionInfo:
    name: str  # name of the connection
    service: str  # e.g. HTTP, TCP, FIX
    protocol: str  # tcp, udp, file
    identifier: Union[int, str, ContextValue]
    direction: Direction

    def to_dict(self):
        return {
            "service": self.service,
            "protocol": self.protocol,
            "identifier": self.identifier,
            "direction": self.direction,
        }

    @property
    def connection(self):
        raise NotImplementedError

    def promote_to_connection(self):
        raise NotImplementedError


class BaseDriverConnection:
    """
    Base class to show connection between drivers.
    Each specific type (protocol) of connection should have its own subclass.
    """

    def __init__(self, driver_connection_info: BaseConnectionInfo):
        self.service = driver_connection_info.service.upper()
        self.connection = driver_connection_info.connection
        self.drivers_listening = defaultdict(list)
        self.drivers_connecting = defaultdict(list)

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: BaseConnectionInfo
    ):
        raise NotImplementedError

    def __str__(self):
        return f"{self.service}-{self.connection}"

    def should_include(self):
        return self.drivers_connecting and self.drivers_listening
