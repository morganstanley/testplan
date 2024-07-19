from socket import SocketKind, AddressFamily
import psutil

from testplan.common.utils.logger import TESTPLAN_LOGGER
from .connection_info import (
    Direction,
    Protocol,
    PortConnectionInfo,
    PortDriverConnection,
    FileConnectionInfo,
    FileDriverConnection,
)

SOCKET_CONNECTION_MAP = {
    SocketKind.SOCK_STREAM: Protocol.TCP,
    SocketKind.SOCK_DGRAM: Protocol.UDP,
}


def get_network_connections(proc: psutil.Process):
    connections = []
    listening_addresses = []
    # update to proc.net_connections when psutil is updated to >=6.0.0
    for conn in proc.connections():
        # first loop to determine which is listening
        if conn.status == psutil.CONN_LISTEN:
            # TODO: account for host types
            listening_addresses.append(conn.laddr.port)

    for conn in proc.connections():
        # second loop to get connections
        if conn.family == AddressFamily.AF_UNIX:
            # ignore unix sockets for now
            continue
        if conn.type == SocketKind.SOCK_SEQPACKET:
            # ignore seqpacket for now
            continue
        if conn.status == psutil.CONN_NONE:
            # UDP sockets
            connections.append(
                PortConnectionInfo(
                    name="Listening port",
                    connectionType=PortDriverConnection,
                    service=SOCKET_CONNECTION_MAP[conn.type],
                    protocol=SOCKET_CONNECTION_MAP[conn.type],
                    identifier=conn.laddr.port,
                    direction=Direction.listening,
                    local_port=conn.laddr.port,
                    local_host=conn.laddr.ip,
                )
            )
        elif conn.status == psutil.CONN_ESTABLISHED:
            if conn.laddr.port in listening_addresses:
                connections.append(
                    PortConnectionInfo(
                        name="Listening port",
                        connectionType=PortDriverConnection,
                        service=SOCKET_CONNECTION_MAP[conn.type],
                        protocol=SOCKET_CONNECTION_MAP[conn.type],
                        identifier=conn.laddr.port,
                        direction=Direction.listening,
                        local_port=conn.laddr.port,
                        local_host=conn.laddr.ip,
                    )
                )
            else:
                connections.append(
                    PortConnectionInfo(
                        name="Connecting port",
                        connectionType=PortDriverConnection,
                        service=SOCKET_CONNECTION_MAP[conn.type],
                        protocol=SOCKET_CONNECTION_MAP[conn.type],
                        identifier=conn.raddr.port,
                        direction=Direction.listening,
                        local_port=conn.laddr.port,
                        local_host=conn.laddr.ip,
                    )
                )
    return connections


def get_file_connections(
    proc: psutil.Process, ignore_files: "list[str]" = ["stdout", "stderr"]
):
    connections = []
    for open_file in proc.open_files():
        if open_file.path.split("/")[-1] in ignore_files:
            continue
        if open_file.mode in ["r", "r+", "a+"]:
            connections.append(
                FileConnectionInfo(
                    name="Reading from file",
                    connectionType=FileDriverConnection,
                    service=Protocol.FILE,
                    protocol=Protocol.FILE,
                    identifier=open_file.path,
                    direction=Direction.listening,
                )
            )
        if open_file.mode in ["w", "a", "r+", "a+"]:
            connections.append(
                FileConnectionInfo(
                    name="Writing from file",
                    connectionType=FileDriverConnection,
                    service=Protocol.FILE,
                    protocol=Protocol.FILE,
                    identifier=open_file.path,
                    direction=Direction.connecting,
                )
            )
    return connections


def get_connections(driver: str, pid: int):
    network_connections = []
    file_connections = []
    try:
        proc = psutil.Process(pid)
        network_connections = get_network_connections(proc)
        file_connections = get_file_connections(proc)
    except psutil.NoSuchProcess as err:
        TESTPLAN_LOGGER.debug(
            f"Error getting metadata for driver {driver}: {err}"
        )
    return network_connections + file_connections
