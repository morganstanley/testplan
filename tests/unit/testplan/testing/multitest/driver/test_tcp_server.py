"""Unit tests for TCP Server driver."""

import os

import pytest

from testplan.common.entity.base import Environment
from testplan.common.utils.context import context
from testplan.common.utils.sockets import Message, Codec
from testplan.common.utils import path
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


@pytest.fixture(scope="module")
def tcp_server():
    """Start and yield a TCP server driver."""
    with path.TemporaryDirectory() as runpath:
        env = Environment()
        server = TCPServer(
            name="server", host="localhost", port=0, runpath=runpath,
        )
        env.add(server)

        with server:
            yield server


@pytest.fixture(scope="module")
def tcp_client(tcp_server):
    """Start and yield a TCP client driver."""
    with path.TemporaryDirectory() as runpath:
        client = TCPClient(
            name="client",
            host=tcp_server.host,
            port=tcp_server.port,
            runpath=runpath,
        )

        with client:
            yield client


def test_basic_runpath():
    """Test runpath of TCP client and server."""
    with path.TemporaryDirectory() as svr_path:
        # Server runpath
        server = TCPServer(name="server", runpath=svr_path)
        assert_obj_runpath(server, svr_path)

        with path.TemporaryDirectory() as cli_path:
            # Client runpath
            client = TCPClient(
                name="client",
                runpath=cli_path,
                host=server._host,
                port=server._port,
            )
            assert_obj_runpath(client, cli_path)


def test_send_receive(tcp_server, tcp_client):
    """Test sending a request and response between client and server."""
    send_receive_message(tcp_server, tcp_client)


def test_send_receive_with_none_context(runpath):
    """
    Test attempting to start a TCP server using context values, with no context
    set. Verify expected ValueError is raised.
    """
    client = TCPClient(
        name="client",
        host=context("server", "{{host}}"),
        port=context("server", "{{port}}"),
        runpath=runpath,
    )
    with pytest.raises(ValueError):
        client.start()


def test_send_receive_with_context(runpath, tcp_server):
    """
    Test starting a TCP client with the host/port information extracted from the
    server via context values.
    """
    client = TCPClient(
        name="context_client",
        host=context("server", "{{host}}"),
        port=context("server", "{{port}}"),
        runpath=runpath,
    )
    tcp_server.context.add(client)

    with client:
        assert client.host
        assert client.port
        send_receive_message(tcp_server, client)


def assert_obj_runpath(obj, runpath):
    """Check runpath before and after starting a driver."""
    assert obj.cfg.runpath in runpath
    assert obj.runpath is None
    assert obj._runpath is None
    with obj:
        assert obj.runpath == runpath
        assert obj._runpath == runpath
        assert os.path.exists(obj.runpath)


def send_receive_message(server, client):
    """
    Common test utility to test sending a request/response exchange between
    client and server.

    Sends:
    Client ---"Hello"---> Server ---"World"---> Client
    """
    msg_data = "Hello"
    msg = Message(data=msg_data, codec=Codec())
    client.send(msg.to_buffer())
    server.accept_connection()
    recv = Message.from_buffer(
        data=server.receive(len(msg.data)), codec=Codec()
    )
    # Server received data
    assert recv.data == msg_data
    msg_data = "World"
    resp = Message(data=msg_data, codec=Codec())
    server.send(resp.to_buffer())
    recv = Message.from_buffer(
        data=client.receive(len(resp.data)), codec=Codec()
    )
    # Client received response
    assert recv.data == msg_data
