from collections import namedtuple
import pytest
import psutil
import socket

from testplan.testing.multitest.driver.connection import (
    Direction,
    Protocol,
    PortConnectionInfo,
    PortDriverConnection,
    get_network_connections
)

addr = namedtuple("addr", ["ip", "port"])
pconn = namedtuple(
    "pconn", ["fd", "family", "type", "laddr", "raddr", "status"]
)


def test_get_network_connections(mocker):
    mocked_output = [
        pconn(
            fd=0,
            family=socket.AddressFamily.AF_INET,
            type=socket.SocketKind.SOCK_STREAM,
            laddr=addr(ip="127.0.0.1", port=0),
            raddr=(),
            status=psutil.CONN_LISTEN
        ),
        pconn(
            fd=1,
            family=socket.AddressFamily.AF_INET,
            type=socket.SocketKind.SOCK_STREAM,
            laddr=addr(ip="127.0.0.1", port=0),
            raddr=addr(ip="127.0.0.1", port=1),
            status=psutil.CONN_ESTABLISHED
        ),
        pconn(
            fd=2,
            family=socket.AddressFamily.AF_INET,
            type=socket.SocketKind.SOCK_DGRAM,
            laddr=addr(ip="127.0.0.1", port=2),
            raddr=(),
            status=psutil.CONN_NONE
        )
    ]
    mocker.patct("psutil.Process.__init__", return_value=None)
    mocker.patct("psutil.Process.connections", return_value=mocked_output)
    conn = get_network_connections(psutil.Process(0))
    assert len(conn) == 2
    assert conn[0] == PortConnectionInfo(
        name="Listening Port",
        connectionType=PortDriverConnection,
        service=Protocol.TCP,
        protocol=Protocol.TCP,
        identifier=0,
        direction=Direction.listening,
        local_port=0,
        local_host="127.0.0.1",
    )
    assert conn[1] == PortConnectionInfo(
        name="Listening Port",
        connectionType=PortDriverConnection,
        service=Protocol.UDP,
        protocol=Protocol.UDP,
        identifier=2,
        direction=Direction.listening,
        local_port=2,
        local_host="127.0.0.1",
    )