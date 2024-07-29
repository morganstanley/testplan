import socket
import sys
from typing import List, Union
import psutil

from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing.multitest.driver.connection.connection_info import (
    Direction,
    Protocol,
    PortConnectionInfo,
    FileConnectionInfo,
)

SOCKET_CONNECTION_MAP = {
    socket.SocketKind.SOCK_STREAM: Protocol.TCP,
    socket.SocketKind.SOCK_DGRAM: Protocol.UDP,
}


def get_network_connections(proc: psutil.Process) -> List[PortConnectionInfo]:
    """
    Extract network communications in subprocess
    """
    connections = []
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
        if conn.type == socket.SocketKind.SOCK_SEQPACKET:
            # ignore seqpacket for now
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
                    local_port=conn.laddr.port,
                    local_host=conn.laddr.ip,
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
                        local_port=conn.laddr.port,
                        local_host=conn.laddr.ip,
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
                        local_port=conn.laddr.port,
                        local_host=conn.laddr.ip,
                    )
                )
    return connections


def get_file_connections(
    proc: psutil.Process, ignore_files: List[str]
) -> List[FileConnectionInfo]:
    """
    Extract file communications in subprocess
    """
    connections = []
    for open_file in proc.open_files():
        if open_file.path.split("/")[-1] in ignore_files:
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
    return connections


def get_connections(
    driver: str, pid: int
) -> List[Union[FileConnectionInfo, PortConnectionInfo]]:
    """
    Extract file and network communications in subprocess
    """
    network_connections = []
    file_connections = []
    try:
        proc = psutil.Process(pid)
        network_connections = get_network_connections(proc)
        file_connections = get_file_connections(proc, ["stdout", "stderr"])
    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
    ) as err:
        TESTPLAN_LOGGER.info(
            f"Error getting metadata for driver {driver}: {err}"
        )
    return network_connections + file_connections
