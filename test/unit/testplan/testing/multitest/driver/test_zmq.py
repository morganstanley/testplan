"""Unit tests for the ZMQServer and ZMQClient drivers."""

import time

from schema import SchemaError
import zmq
import pytest

from testplan.testing.multitest.driver.zmq import ZMQServer, ZMQClient
from testplan.common.utils.context import context
from testplan.common.utils.timing import TimeoutException
from testplan.common.entity.base import Environment

TIMEOUT = 10


def create_server(name, host, port, message_pattern):
    server = ZMQServer(name=name,
                       host=host,
                       port=port,
                       message_pattern=message_pattern)
    server.start()
    server._wait_started()
    return server


def create_client(name, hosts, ports, message_pattern):
    client = ZMQClient(name=name,
                       hosts=hosts,
                       ports=ports,
                       message_pattern=message_pattern)
    client.start()
    client._wait_started()
    # This will only effect Subscribe clients, necessary to subscribe to all
    # messages.
    client.subscribe(b'')
    return client

def stop_devices(devices):
    for device in devices:
        device.stop()
        device._wait_stopped()


def send_receive_message(sender, receiver, data):
    """
    Sender ---data---> Receiver
    """
    sender.send(data=data, timeout=TIMEOUT)
    recv = receiver.receive(timeout=TIMEOUT)
    assert recv == data


def server_client_logic(server_message_pattern, client_message_pattern):
    server = create_server('server', '127.0.0.1', 0, server_message_pattern)
    client = create_client('client', [server.host], [server.port],
                           client_message_pattern)
    if client_message_pattern == zmq.SUB:
        # The SUB client seems to take longer to connect and results in dropped
        # messages.
        time.sleep(1)

    if ((server_message_pattern == zmq.PAIR) or
        (server_message_pattern == zmq.REP)):
        send_receive_message(sender=client, receiver=server, data=b'Hello')
        send_receive_message(sender=server, receiver=client, data=b'World')
    else:
        send_receive_message(sender=server, receiver=client,
                             data=b'Hello World')

    stop_devices([client, server])


def test_create_client_with_context():
    rcxt = Environment()
    server = ZMQServer(name='server', host='127.0.0.1', port=0,
                       message_pattern=zmq.PAIR)
    rcxt.add(server)
    client = ZMQClient(name='client', hosts=[context('server', '{{host}}')],
                       ports=[context('server', '{{port}}')],
                       message_pattern=zmq.PAIR)
    rcxt.add(client)

    assert server.port is None
    for item in rcxt:
        item.start()
        item._wait_started()
    assert server.port != 0
    assert client.ports != 0

    send_receive_message(sender=client, receiver=server, data=b'Hello World')
    stop_devices(reversed(list(rcxt)))


def test_pair_send_recv():
    server_client_logic(server_message_pattern=zmq.PAIR,
                        client_message_pattern=zmq.PAIR)


def test_request_reply():
    server_client_logic(server_message_pattern=zmq.REP,
                        client_message_pattern=zmq.REQ)


def test_one_request_many_reply():
    server1 = create_server('server1', '127.0.0.1', 0, zmq.REP)
    server2 = create_server('server2', '127.0.0.1', 0, zmq.REP)
    client = create_client('client', [server1.host, server2.host],
                           [server1.port, server2.port], zmq.REQ)

    send_receive_message(sender=client, receiver=server1, data=b'Hello 1')
    send_receive_message(sender=server1, receiver=client, data=b'World 1')
    send_receive_message(sender=client, receiver=server2, data=b'Hello 2')
    send_receive_message(sender=server2, receiver=client, data=b'World 2')

    stop_devices([server1, server2, client])


def test_many_request_one_reply():
    server = create_server('server', '127.0.0.1', 0, zmq.REP)
    client1 = create_client('client1', [server.host], [server.port], zmq.REQ)
    client2 = create_client('client2', [server.host], [server.port], zmq.REQ)

    send_receive_message(sender=client1, receiver=server, data=b'Hello 1')
    send_receive_message(sender=server, receiver=client1, data=b'World 1')
    send_receive_message(sender=client2, receiver=server, data=b'Hello 2')
    send_receive_message(sender=server, receiver=client2, data=b'World 2')

    stop_devices([server, client1, client2])


def test_publish_subscribe():
    server_client_logic(server_message_pattern=zmq.PUB,
                        client_message_pattern=zmq.SUB)


def test_one_publish_many_subscribe():
    server = create_server('server', '127.0.0.1', 0, zmq.PUB)
    client1 = create_client('client1', [server.host], [server.port], zmq.SUB)
    client2 = create_client('client2', [server.host], [server.port], zmq.SUB)
    # The SUB client seems to take longer to connect and results in dropped
    # messages.
    time.sleep(1)

    data = b'Hello World'
    server.send(data=data, timeout=TIMEOUT)
    recv1 = client1.receive(timeout=TIMEOUT)
    recv2 = client2.receive(timeout=TIMEOUT)

    assert data == recv1
    assert data == recv2

    stop_devices([server, client1, client2])


def test_many_publish_one_subscribe():
    server1 = create_server('server1', '127.0.0.1', 0, zmq.PUB)
    server2 = create_server('server2', '127.0.0.1', 0, zmq.PUB)
    client = create_client('client', [server1.host, server2.host],
                           [server1.port, server2.port], zmq.SUB)
    # The SUB client seems to take longer to connect and results in dropped
    # messages.
    time.sleep(1)

    data1 = b'Hello'
    data2 = b'World'
    server1.send(data=data1, timeout=TIMEOUT)
    recv1 = client.receive(timeout=TIMEOUT)
    server2.send(data=data2, timeout=TIMEOUT)
    recv2 = client.receive(timeout=TIMEOUT)
    assert data1 == recv1
    assert data2 == recv2

    stop_devices([server1, server2, client])


def test_push_pull():
    server_client_logic(server_message_pattern=zmq.PUSH,
                        client_message_pattern=zmq.PULL)


def test_many_push_one_pull():
    server1 = create_server('server1', '127.0.0.1', 0, zmq.PUSH)
    server2 = create_server('server2', '127.0.0.1', 0, zmq.PUSH)
    client = create_client('client', [server1.host, server2.host],
                           [server1.port, server2.port], zmq.PULL)
    time.sleep(1)

    data1 = b'Hello'
    data2 = b'World'
    server1.send(data=data1, timeout=TIMEOUT)
    recv1 = client.receive(timeout=TIMEOUT)
    server2.send(data=data2, timeout=TIMEOUT)
    recv2 = client.receive(timeout=TIMEOUT)
    assert data1 == recv1
    assert data2 == recv2

    stop_devices([server1, server2, client])


def test_message_pattern_type():
    server_args = {'name':'server',
                   'host':'localhost',
                   'port':0}
    pytest.raises(SchemaError, ZMQServer,
                  kwargs=dict(server_args, **{'message_pattern':zmq.REQ}))
    pytest.raises(SchemaError, ZMQServer,
                  kwargs=dict(server_args, **{'message_pattern':zmq.SUB}))
    pytest.raises(SchemaError, ZMQServer,
                  kwargs=dict(server_args, **{'message_pattern':zmq.PULL}))
    client_args = {'name':'client',
                   'hosts':['localhost'],
                   'ports':[0],
                   'connect_at_start':False}
    pytest.raises(SchemaError, ZMQClient,
                  kwargs=dict(client_args, **{'message_pattern':zmq.REP}))
    pytest.raises(SchemaError, ZMQClient,
                  kwargs=dict(client_args, **{'message_pattern':zmq.PUB}))
    pytest.raises(SchemaError, ZMQClient,
                  kwargs=dict(client_args, **{'message_pattern':zmq.PUSH}))


def test_subscribe():
    server = create_server('server', '127.0.0.1', 0, zmq.PUB)
    client = create_client('client', [server.host], [server.port], zmq.SUB)
    client.unsubscribe(b'')
    client.subscribe(b'Hello')
    time.sleep(1)

    data1 = b'Hello World'
    data2 = b'random message'
    server.send(data= data1, timeout=TIMEOUT)
    recv = client.receive(timeout=TIMEOUT)
    assert data1 == recv
    server.send(data=data2, timeout=TIMEOUT)
    with pytest.raises(TimeoutException):
        client.receive(timeout=0.2)

    stop_devices([server, client])


def test_flush():
    server = create_server('server', '127.0.0.1', 0, zmq.PAIR)
    client = create_client('client', [server.host], [server.port], zmq.PAIR)

    client.send(data=b'Hello World', timeout=TIMEOUT)
    server.receive(timeout=TIMEOUT)
    server.send(data=b'Hello client', timeout=TIMEOUT)
    client.flush()

    with pytest.raises(TimeoutException):
        client.receive(timeout=0.2)

    stop_devices([server, client])
