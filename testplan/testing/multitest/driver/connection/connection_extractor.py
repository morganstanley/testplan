import socket
import sys
from typing import List
import psutil

from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing.multitest.driver.connection.base import (
    BaseConnectionExtractor,
    Direction,
)
from testplan.testing.multitest.driver.connection.connection_info import (
    Protocol,
    PortConnectionInfo,
    FileConnectionInfo,
)


SOCKET_CONNECTION_MAP = {
    socket.SocketKind.SOCK_STREAM: Protocol.TCP,
    socket.SocketKind.SOCK_DGRAM: Protocol.UDP,
}

NETWORK_CONNECTION_MAP = {
    Protocol.TCP: socket.SocketKind.SOCK_STREAM,
    Protocol.UDP: socket.SocketKind.SOCK_DGRAM,
}


class ConnectionExtractor(BaseConnectionExtractor):
    def __init__(
        self, service: str, protocol: Protocol, direction: Direction
    ) -> None:
        self.service = service
        self.protocol = protocol
        self.direction = direction

    def extract_connection(self, driver) -> List[PortConnectionInfo]:

        return [
            PortConnectionInfo(
                name="Port",
                service=self.service,
                protocol=self.protocol,
                direction=self.direction,
                identifier=driver.connection_identifier,
                port=getattr(driver, "local_port", None),
                host=getattr(driver, "local_host", None),
            )
        ]


class PortConnectionExtractor(BaseConnectionExtractor):
    def __init__(
        self,
        connections_to_check: List[Protocol] = None,
        connections_to_ignore: List[Protocol] = None,
    ):
        if not connections_to_check:
            connections_to_check = [Protocol.TCP, Protocol.UDP]
        if not connections_to_ignore:
            connections_to_ignore = []
        # map the protocols to SocketKind
        for (idx, protocol) in enumerate(connections_to_check):
            connections_to_check[idx] = NETWORK_CONNECTION_MAP[protocol]
        for (idx, protocol) in enumerate(connections_to_ignore):
            connections_to_ignore[idx] = NETWORK_CONNECTION_MAP[protocol]
        connections_to_ignore.append(socket.SocketKind.SOCK_SEQPACKET)
        self.connections_to_check = connections_to_check
        self.connections_to_ignore = connections_to_ignore

    def extract_connection(self, driver) -> List[PortConnectionInfo]:
        connections = []
        try:
            proc = psutil.Process(driver.pid)
            listening_addresses = []
            # update to net_connections when psutil is updated to 6.0.0
            for conn in proc.connections():
                # first loop to determine which is listening
                if conn.status == psutil.CONN_LISTEN:
                    # TODO: account for host types
                    listening_addresses.append(conn.laddr.port)

            for conn in proc.connections():
                # second loop to get connections
                if (
                    sys.platform != "win32"
                    and conn.family == socket.AddressFamily.AF_UNIX
                ):
                    # ignore unix sockets for now
                    continue
                if (
                    conn.type not in self.connections_to_check
                    or conn.type in self.connections_to_ignore
                ):
                    continue
                if conn.status == psutil.CONN_NONE:
                    # UDP sockets
                    connections.append(
                        PortConnectionInfo(
                            name="Listening port",
                            service=SOCKET_CONNECTION_MAP[conn.type],
                            protocol=SOCKET_CONNECTION_MAP[conn.type],
                            identifier=conn.laddr.port,
                            direction=Direction.LISTENING,
                            port=conn.laddr.port,
                            host=conn.laddr.ip,
                        )
                    )
                elif conn.status == psutil.CONN_ESTABLISHED:
                    if conn.laddr.port in listening_addresses:
                        connections.append(
                            PortConnectionInfo(
                                name="Listening port",
                                service=SOCKET_CONNECTION_MAP[conn.type],
                                protocol=SOCKET_CONNECTION_MAP[conn.type],
                                identifier=conn.laddr.port,
                                direction=Direction.LISTENING,
                                port=conn.laddr.port,
                                host=conn.laddr.ip,
                            )
                        )
                    else:
                        connections.append(
                            PortConnectionInfo(
                                name="Connecting port",
                                service=SOCKET_CONNECTION_MAP[conn.type],
                                protocol=SOCKET_CONNECTION_MAP[conn.type],
                                identifier=conn.raddr.port,
                                direction=Direction.CONNECTING,
                                port=conn.laddr.port,
                                host=conn.laddr.ip,
                            )
                        )
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ) as err:
            TESTPLAN_LOGGER.info(
                f"Error getting metadata for driver {str(driver)}: {err}"
            )
        return connections


class FileConnectionExtractor(BaseConnectionExtractor):
    def __init__(self, files_to_ignore: List[str] = None):
        if not files_to_ignore:
            files_to_ignore = ["stdout", "stderr"]
        self.files_to_ignore = files_to_ignore

    def extract_connection(self, driver) -> List[FileConnectionInfo]:
        connections = []
        try:
            proc = psutil.Process(driver.pid)
            for open_file in proc.open_files():
                if open_file.path.split("/")[-1] in self.files_to_ignore:
                    continue
                if open_file.mode in ["r", "r+", "a+"]:
                    connections.append(
                        FileConnectionInfo(
                            name="Reading from file",
                            service=Protocol.FILE,
                            protocol=Protocol.FILE,
                            identifier=open_file.path,
                            direction=Direction.LISTENING,
                        )
                    )
                if open_file.mode in ["w", "a", "r+", "a+"]:
                    connections.append(
                        FileConnectionInfo(
                            name="Writing to file",
                            service=Protocol.FILE,
                            protocol=Protocol.FILE,
                            identifier=open_file.path,
                            direction=Direction.CONNECTING,
                        )
                    )
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ) as err:
            TESTPLAN_LOGGER.info(
                f"Error getting metadata for driver {str(driver)}: {err}"
            )
        return connections
