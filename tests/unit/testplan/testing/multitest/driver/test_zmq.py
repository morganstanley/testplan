"""Unit tests for the ZMQServer and ZMQClient drivers."""

import os
import time

from schema import SchemaError
import zmq
import pytest

from testplan.testing.multitest.driver.zmq import ZMQServer, ZMQClient
from testplan.common.utils.context import context
from testplan.common.utils.timing import TimeoutException
from testplan.common.entity.base import Environment

TIMEOUT = 10


@pytest.mark.parametrize(
    "server_message_pattern,client_message_pattern",
    [
        (zmq.PAIR, zmq.PAIR),
        (zmq.REP, zmq.REQ),
        (zmq.PUB, zmq.SUB),
        (zmq.PUSH, zmq.PULL),
    ],
)
def test_send_receive(server_message_pattern, client_message_pattern, runpath):
    """Test sending message between server and client."""
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=server_message_pattern,
        runpath=os.path.join(runpath, "server"),
    )
    with server:
        client = ZMQClient(
            name="client",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=client_message_pattern,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            if client_message_pattern == zmq.SUB:
                client.subscribe(b"")

                # The SUB client seems to take longer to connect and results in
                # dropped messages.
                time.sleep(1)

            if (server_message_pattern == zmq.PAIR) or (
                server_message_pattern == zmq.REP
            ):
                send_receive_message(
                    sender=client, receiver=server, data=b"Hello"
                )
                send_receive_message(
                    sender=server, receiver=client, data=b"World"
                )
            else:
                send_receive_message(
                    sender=server, receiver=client, data=b"Hello World"
                )


def test_create_client_with_context(runpath):
    """
    Test creating a client that extracts its host and port from the context.
    """
    env = Environment()
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PAIR,
        runpath=os.path.join(runpath, "server"),
    )
    env.add(server)
    client = ZMQClient(
        name="client",
        hosts=[context("server", "{{host}}")],
        ports=[context("server", "{{port}}")],
        message_pattern=zmq.PAIR,
        runpath=os.path.join(runpath, "client"),
    )
    env.add(client)

    assert server.port is None

    with env:
        assert server.port != 0
        assert client.ports != 0
        send_receive_message(
            sender=client, receiver=server, data=b"Hello World"
        )


def test_one_request_many_reply(runpath):
    """Test connecting a request client to two reply servers."""
    server1 = ZMQServer(
        name="server1",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.REP,
        runpath=os.path.join(runpath, "server1"),
    )
    server2 = ZMQServer(
        name="server2",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.REP,
        runpath=os.path.join(runpath, "server2"),
    )

    with server1, server2:
        client = ZMQClient(
            name="client",
            hosts=[server1.host, server2.host],
            ports=[server1.port, server2.port],
            message_pattern=zmq.REQ,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            send_receive_message(
                sender=client, receiver=server1, data=b"Hello 1"
            )
            send_receive_message(
                sender=server1, receiver=client, data=b"World 1"
            )
            send_receive_message(
                sender=client, receiver=server2, data=b"Hello 2"
            )
            send_receive_message(
                sender=server2, receiver=client, data=b"World 2"
            )


def test_many_request_one_reply(runpath):
    """Test connecting two request clients to a reply server."""
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.REP,
        runpath=os.path.join(runpath, "server"),
    )

    with server:
        client1 = ZMQClient(
            name="client1",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.REQ,
            runpath=os.path.join(runpath, "client1"),
        )
        client2 = ZMQClient(
            name="client2",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.REQ,
            runpath=os.path.join(runpath, "client2"),
        )

        with client1, client2:
            send_receive_message(
                sender=client1, receiver=server, data=b"Hello 1"
            )
            send_receive_message(
                sender=server, receiver=client1, data=b"World 1"
            )
            send_receive_message(
                sender=client2, receiver=server, data=b"Hello 2"
            )
            send_receive_message(
                sender=server, receiver=client2, data=b"World 2"
            )


def test_one_publish_many_subscribe(runpath):
    """Test connecting two subscribe clients to one publish server."""
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUB,
        runpath=os.path.join(runpath, "server"),
    )

    with server:
        client1 = ZMQClient(
            name="client1",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.SUB,
            runpath=os.path.join(runpath, "client1"),
        )
        client2 = ZMQClient(
            name="client2",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.SUB,
            runpath=os.path.join(runpath, "client2"),
        )

        with client1, client2:
            for client in (client1, client2):
                client.subscribe(b"")

            # The SUB client seems to take longer to connect and results in
            # dropped messages.
            time.sleep(1)

            data = b"Hello World"
            server.send(data=data, timeout=TIMEOUT)
            recv1 = client1.receive(timeout=TIMEOUT)
            recv2 = client2.receive(timeout=TIMEOUT)

            assert data == recv1
            assert data == recv2


def test_many_publish_one_subscribe(runpath):
    """Test connecting one subscribe client to two publish servers."""
    server1 = ZMQServer(
        name="server1",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUB,
        runpath=os.path.join(runpath, "server1"),
    )
    server2 = ZMQServer(
        name="server2",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUB,
        runpath=os.path.join(runpath, "server2"),
    )

    with server1, server2:
        client = ZMQClient(
            name="client",
            hosts=[server1.host, server2.host],
            ports=[server1.port, server2.port],
            message_pattern=zmq.SUB,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            client.subscribe(b"")

            # The SUB client seems to take longer to connect and results in
            # dropped messages.
            time.sleep(1)

            data1 = b"Hello"
            data2 = b"World"
            server1.send(data=data1, timeout=TIMEOUT)
            recv1 = client.receive(timeout=TIMEOUT)
            server2.send(data=data2, timeout=TIMEOUT)
            recv2 = client.receive(timeout=TIMEOUT)
            assert data1 == recv1
            assert data2 == recv2


def test_many_push_one_pull(runpath):
    """Test connecting one pull client to two push servers."""
    server1 = ZMQServer(
        name="server1",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUSH,
        runpath=os.path.join(runpath, "server1"),
    )
    server2 = ZMQServer(
        name="server2",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUSH,
        runpath=os.path.join(runpath, "server2"),
    )

    with server1, server2:
        client = ZMQClient(
            name="client",
            hosts=[server1.host, server2.host],
            ports=[server1.port, server2.port],
            message_pattern=zmq.PULL,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            time.sleep(1)

            data1 = b"Hello"
            data2 = b"World"
            server1.send(data=data1, timeout=TIMEOUT)
            recv1 = client.receive(timeout=TIMEOUT)
            server2.send(data=data2, timeout=TIMEOUT)
            recv2 = client.receive(timeout=TIMEOUT)
            assert data1 == recv1
            assert data2 == recv2


def test_message_pattern_type():
    """Test schema errors are raised for incorrect pattern types.."""
    server_args = {"name": "server", "host": "localhost", "port": 0}

    with pytest.raises(SchemaError):
        ZMQServer(message_pattern=zmq.REQ, **server_args)

    with pytest.raises(SchemaError):
        ZMQServer(message_pattern=zmq.SUB, **server_args)

    with pytest.raises(SchemaError):
        ZMQServer(message_pattern=zmq.PULL, **server_args)

    client_args = {
        "name": "client",
        "hosts": ["localhost"],
        "ports": [0],
        "connect_at_start": False,
    }

    with pytest.raises(SchemaError):
        ZMQClient(message_pattern=zmq.REP, **client_args)

    with pytest.raises(SchemaError):
        ZMQClient(message_pattern=zmq.PUB, **client_args)

    with pytest.raises(SchemaError):
        ZMQClient(message_pattern=zmq.PUSH, **client_args)


def test_subscribe(runpath):
    """Test subscribing to a particular data format."""
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PUB,
        runpath=os.path.join(runpath, "server"),
    )

    with server:
        client = ZMQClient(
            name="client",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.SUB,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            client.subscribe(b"Hello")
            time.sleep(1)

            data1 = b"Hello World"
            data2 = b"random message"
            server.send(data=data1, timeout=TIMEOUT)
            recv = client.receive(timeout=TIMEOUT)
            assert data1 == recv
            server.send(data=data2, timeout=TIMEOUT)
            with pytest.raises(TimeoutException):
                client.receive(timeout=0.2)


def test_flush(runpath):
    """Test flushing the client receive queue."""
    server = ZMQServer(
        name="server",
        host="127.0.0.1",
        port=0,
        message_pattern=zmq.PAIR,
        runpath=os.path.join(runpath, "server"),
    )

    with server:
        client = ZMQClient(
            name="client",
            hosts=[server.host],
            ports=[server.port],
            message_pattern=zmq.PAIR,
            runpath=os.path.join(runpath, "client"),
        )

        with client:
            client.send(data=b"Hello World", timeout=TIMEOUT)
            server.receive(timeout=TIMEOUT)
            server.send(data=b"Hello client", timeout=TIMEOUT)
            client.flush()

            with pytest.raises(TimeoutException):
                client.receive(timeout=0.2)


def send_receive_message(sender, receiver, data):
    """
    Utility function to send a mesage from sender to receiver and assert it
    is received correctly.

    Sender ---data---> Receiver
    """
    sender.send(data=data, timeout=TIMEOUT)
    recv = receiver.receive(timeout=TIMEOUT)
    assert recv == data
