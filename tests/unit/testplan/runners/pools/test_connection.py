"""CURVE authentication happens before the application can deserialize."""

import dataclasses
import io
from types import SimpleNamespace

import pytest
import zmq
from zmq.utils.monitor import recv_monitor_message

from testplan.common.utils.zmq_security import (
    CurveServerKeys,
    read_curve_keys,
    write_curve_keys,
)
from testplan.runners.pools import connection
from testplan.runners.pools.communication import Message


@pytest.fixture
def server():
    srv = connection.ZMQServer()
    srv.parent = SimpleNamespace(cfg=SimpleNamespace(host="127.0.0.1", port=0))
    srv.start()
    yield srv
    srv.stop()


@pytest.mark.parametrize(
    "intruder", ["plaintext", "wrong-client", "wrong-pin"]
)
def test_rejects_intruders_before_deserialization(server, intruder, mocker):
    spy = mocker.spy(connection, "deserialize")
    context = zmq.Context()
    rogue = context.socket(zmq.REQ)
    rogue.linger = 0
    rogue.handshake_ivl = 500
    monitor = server.sock.get_monitor_socket(
        events=zmq.EVENT_HANDSHAKE_FAILED_AUTH
        | zmq.EVENT_HANDSHAKE_FAILED_PROTOCOL
        | zmq.EVENT_HANDSHAKE_FAILED_NO_DETAIL
        | zmq.EVENT_HANDSHAKE_SUCCEEDED
    )
    other = CurveServerKeys().client_keys
    if intruder == "wrong-client":
        dataclasses.replace(
            other, server_public=server.client_keys.server_public
        ).configure(rogue)
    elif intruder == "wrong-pin":
        dataclasses.replace(
            server.client_keys, server_public=other.server_public
        ).configure(rogue)
    client = None
    try:
        # Connect only the intruder until its handshake has actually failed.
        rogue.connect(f"tcp://{server.address}")
        rogue.send(b"untrusted serialized input")
        assert monitor.poll(3000), "No handshake outcome"
        event = recv_monitor_message(monitor)["event"]
        assert event != zmq.EVENT_HANDSHAKE_SUCCEEDED
        assert server.accept() is None
        spy.assert_not_called()

        client = connection.ZMQClient(server.address, server.client_keys)
        for value in (17, 29):
            client.send(Message(index="worker").make(Message.Heartbeat, value))
            assert server.sock.poll(3000)
            request = server.accept()
            assert request.cmd == Message.Heartbeat
            assert request.data == value
            proxy = connection.ZMQClientProxy()
            proxy.connect(server)
            proxy.respond(Message().make(Message.Ack, value + 1))
            reply = client.receive()
            assert reply.cmd == Message.Ack
            assert reply.data == value + 1
        assert spy.call_count == 4
    finally:
        if client is not None:
            client.disconnect()
        rogue.close()
        monitor.close()
        server.sock.disable_monitor()
        context.term()


def test_client_rejects_impostor_server(server, mocker):
    spy = mocker.spy(connection, "deserialize")
    # Correct client identity but the public key of a different server.
    keys = dataclasses.replace(
        server.client_keys,
        server_public=CurveServerKeys().client_keys.server_public,
    )
    client = connection.ZMQClient(server.address, keys, recv_timeout=0.5)
    try:
        client.send(Message(index="worker").make(Message.Heartbeat))
        assert client.receive() is None
        assert server.accept() is None
        spy.assert_not_called()
    finally:
        client.disconnect()


def test_server_stops_authenticator_and_restarts(server):
    auth = server._authenticator
    server.stop()
    assert not auth.is_alive()
    assert server._zmq_context is None
    server.start()
    assert server._authenticator.is_alive()


def test_bind_failure_closes_authenticator(server):
    other = connection.ZMQServer()
    other.parent = SimpleNamespace(
        cfg=SimpleNamespace(
            host="127.0.0.1", port=int(server.address.split(":")[1])
        )
    )
    with pytest.raises(zmq.ZMQError):
        other.starting()
    assert other._authenticator is None
    assert other._zmq_context is None
    assert other.sock is None


@pytest.mark.parametrize("prefix", [b"", b"y\n"])
def test_bootstrap_roundtrip_without_server_secret(prefix):
    pool, monitor = CurveServerKeys(), CurveServerKeys()
    channels = {
        "pool": pool.client_keys,
        "resource_monitor": monitor.client_keys,
    }
    stream = io.BytesIO()
    stream.write(prefix)
    write_curve_keys(stream, channels)
    assert pool._secret not in stream.getvalue()
    assert monitor._secret not in stream.getvalue()
    stream.seek(0)
    assert read_curve_keys(stream) == channels
    assert pool.client_keys.client_secret not in repr(pool.client_keys)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"y\n",
        b"TESTPLAN_CURVE secret-not-json\n",
        b"TESTPLAN_CURVE []\n",
        b'TESTPLAN_CURVE {"pool": {"client_secret": "exposed-secret"}}\n',
    ],
)
def test_invalid_bootstrap_fails_without_disclosing_keys(payload):
    with pytest.raises(ValueError) as exc:
        read_curve_keys(io.BytesIO(payload))
    assert "exposed-secret" not in str(exc.value)
    assert "secret-not-json" not in str(exc.value)


def test_missing_curve_support_fails_closed(monkeypatch):
    monkeypatch.setattr(zmq, "has", lambda feature: False)
    with pytest.raises(RuntimeError, match="CURVE support"):
        connection.ZMQServer()
