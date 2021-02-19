"""TODO."""

from testplan.common.utils.sockets import Server, Client


def test_basic_server_client():
    # Start server
    server = Server()
    server.bind()
    assert server._listening is False
    server.serve()
    assert server._listening is True
    assert server.active_connections == 0
    assert server.accepted_connections == 0

    # No connection to accept
    assert server.accept_connection(timeout=0) == -1

    # Connect client
    client = Client(host=server.ip, port=server.port)
    client.connect()

    # Server accepts connection
    conn_idx = server.accept_connection()
    assert conn_idx == 0
    assert server.active_connections == 1
    assert server.accepted_connections == 1

    # Client sends message
    msg = b"Hello"
    _, size = client.send(msg)
    assert size == len(msg)

    # Server receives
    received = server.receive(size, conn_idx=conn_idx)
    assert received == msg

    # Server sends reply
    msg = b"World"
    server.send(msg, conn_idx)
    received = client.receive(1024)
    assert received == msg

    client.close()
    server.close()


def test_two_clients():
    server = Server()
    server.bind()
    server.serve()

    client1 = Client(host=server.ip, port=server.port)
    client2 = Client(host=server.ip, port=server.port)

    # Client 1 connect and send message
    client1.connect()
    conn_1 = server.accept_connection(5)
    msg1 = b"Hello!"
    _, size1 = client1.send(msg1)

    # Client 2 connect and send message before server received msg from 1
    client2.connect()
    conn_2 = server.accept_connection(5)
    msg2 = b"Hey"
    _, size2 = client2.send(msg2)

    # Server responds to 1
    assert server.receive(size1, conn_idx=conn_1) == msg1
    resp1 = b"Yo1"
    server.send(resp1, conn_idx=conn_1)

    # Server responds to 2
    assert server.receive(size2, conn_idx=conn_2) == msg2
    resp2 = b"Yo2"
    server.send(resp2, conn_idx=conn_2)

    # Clients receiving responses
    assert client1.recv(1024) == resp1
    assert client2.recv(1024) == resp2

    client1.close()
    client2.close()
    server.close()
