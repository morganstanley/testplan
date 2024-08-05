from collections import namedtuple
import pytest
import psutil
import socket
from unittest.mock import MagicMock

from testplan.testing.multitest.driver.connection import (
    Direction,
    Protocol,
    PortConnectionInfo,
    PortConnectionExtractor,
    FileConnectionInfo,
    FileConnectionExtractor,
)
from pytest_test_filters import skip_on_windows


addr = namedtuple("addr", ["ip", "port"])
pconn = namedtuple(
    "pconn", ["fd", "family", "type", "laddr", "raddr", "status"]
)
popenfile = namedtuple("popenfile", ["path", "mode"])


@skip_on_windows(
    reason="psutil/socket has different functions and attributes on Windows."
)
class TestPortConnectionExtractor:
    def test_extract_connections(self, mocker):
        mocked_output = [
            pconn(
                fd=0,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_STREAM,
                laddr=addr(ip="127.0.0.1", port=0),
                raddr=(),
                status=psutil.CONN_LISTEN,
            ),
            pconn(
                fd=1,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_STREAM,
                laddr=addr(ip="127.0.0.1", port=0),
                raddr=addr(ip="127.0.0.1", port=1),
                status=psutil.CONN_ESTABLISHED,
            ),
            pconn(
                fd=2,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_DGRAM,
                laddr=addr(ip="127.0.0.1", port=2),
                raddr=(),
                status=psutil.CONN_NONE,
            ),
        ]
        mocker.patch("psutil.Process.__init__", return_value=None)
        mocker.patch("psutil.Process.connections", return_value=mocked_output)
        driver = MagicMock()
        driver.pid = 0
        extractor = PortConnectionExtractor()
        conn = extractor.extract_connection(driver)
        assert len(conn) == 2
        assert conn[0] == PortConnectionInfo(
            name="Listening port",
            service=Protocol.TCP,
            protocol=Protocol.TCP,
            identifier=0,
            direction=Direction.LISTENING,
            port=0,
            host="127.0.0.1",
        )
        assert conn[1] == PortConnectionInfo(
            name="Listening port",
            service=Protocol.UDP,
            protocol=Protocol.UDP,
            identifier=2,
            direction=Direction.LISTENING,
            port=2,
            host="127.0.0.1",
        )

    def test_ignore_connections(self, mocker):
        mocked_output = [
            pconn(
                fd=0,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_STREAM,
                laddr=addr(ip="127.0.0.1", port=0),
                raddr=(),
                status=psutil.CONN_LISTEN,
            ),
            pconn(
                fd=1,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_STREAM,
                laddr=addr(ip="127.0.0.1", port=0),
                raddr=addr(ip="127.0.0.1", port=1),
                status=psutil.CONN_ESTABLISHED,
            ),
            pconn(
                fd=2,
                family=socket.AddressFamily.AF_INET,
                type=socket.SocketKind.SOCK_DGRAM,
                laddr=addr(ip="127.0.0.1", port=2),
                raddr=(),
                status=psutil.CONN_NONE,
            ),
        ]
        mocker.patch("psutil.Process.__init__", return_value=None)
        mocker.patch("psutil.Process.connections", return_value=mocked_output)
        driver = MagicMock()
        driver.pid = 0
        extractor = PortConnectionExtractor(
            connections_to_ignore=[Protocol.UDP]
        )
        conn = extractor.extract_connection(driver)
        assert len(conn) == 1
        assert conn[0] == PortConnectionInfo(
            name="Listening port",
            service=Protocol.TCP,
            protocol=Protocol.TCP,
            identifier=0,
            direction=Direction.LISTENING,
            port=0,
            host="127.0.0.1",
        )

        extractor = PortConnectionExtractor(
            connections_to_ignore=[Protocol.TCP]
        )
        conn = extractor.extract_connection(driver)
        assert len(conn) == 1
        assert conn[0] == PortConnectionInfo(
            name="Listening port",
            service=Protocol.UDP,
            protocol=Protocol.UDP,
            identifier=2,
            direction=Direction.LISTENING,
            port=2,
            host="127.0.0.1",
        )


@skip_on_windows(
    reason="psutil/socket has different functions and attributes on Windows."
)
class TestPortConnectionExtractor:
    def test_extract_connections(self, mocker):
        mocked_output = [
            popenfile(path="test/stdout", mode="w"),
            popenfile(path="test/log", mode="r+"),
        ]
        mocker.patch("psutil.Process.__init__", return_value=None)
        mocker.patch("psutil.Process.open_files", return_value=mocked_output)
        driver = MagicMock()
        driver.pid = 0
        extractor = FileConnectionExtractor()
        conn = extractor.extract_connection(driver)
        assert len(conn) == 2
        assert conn[0] == FileConnectionInfo(
            name="Reading from file",
            service=Protocol.FILE,
            protocol=Protocol.FILE,
            identifier="test/log",
            direction=Direction.LISTENING,
        )
        assert conn[1] == FileConnectionInfo(
            name="Writing to file",
            service=Protocol.FILE,
            protocol=Protocol.FILE,
            identifier="test/log",
            direction=Direction.CONNECTING,
        )

    def test_ignore_files(self, mocker):
        mocked_output = [
            popenfile(path="test/stdout", mode="w"),
            popenfile(path="test/log", mode="r+"),
        ]
        mocker.patch("psutil.Process.__init__", return_value=None)
        mocker.patch("psutil.Process.open_files", return_value=mocked_output)
        driver = MagicMock()
        driver.pid = 0
        extractor = FileConnectionExtractor("log")
        conn = extractor.extract_connection(driver)
        assert len(conn) == 1
        assert conn[0] == FileConnectionInfo(
            name="Writing to file",
            service=Protocol.FILE,
            protocol=Protocol.FILE,
            identifier="test/stdout",
            direction=Direction.CONNECTING,
        )
