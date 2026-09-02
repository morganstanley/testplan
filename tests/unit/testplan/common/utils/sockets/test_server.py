"""TODO."""

import multiprocessing
import socket
import threading

from testplan.common.utils.sockets import Server, Client

from pytest_test_filters import skip_on_windows


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


def _run_test_reconnect_while_closing_connection():
    server = Server()
    server.bind()
    server.serve()

    # new fd
    first_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # new fd
    second_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    close_started = threading.Event()
    resume_close = threading.Event()
    close_errors = []

    first_client.connect((server.ip, server.port))
    first_conn_idx = server.accept_connection()
    # this fd should be reused
    first_fdesc = server._fds[first_conn_idx]
    first_conn = server._connection_by_fd[first_fdesc]

    class _SlowCloseDouble:
        def close(self):
            first_conn.close()
            close_started.set()
            if not resume_close.wait(timeout=5):
                raise TimeoutError("Timed out waiting to finish socket close")

    server._connection_by_fd[first_fdesc] = _SlowCloseDouble()

    def close_connection():
        try:
            server.close_connection(first_conn_idx)
        except Exception as exc:  # pylint: disable=broad-except
            close_errors.append(exc)

    close_thread = threading.Thread(target=close_connection)
    close_thread.start()

    try:
        assert close_started.wait(timeout=5)

        # This socket was created before the first connection closed, leaving
        # the server-side fd of first connection as the lowest available fd
        # for accept()
        second_client.connect((server.ip, server.port))
        second_conn_idx = server.accept_connection(
            timeout=5, accept_connection_sleep=0.01
        )
        assert second_conn_idx != -1
        assert server._fds[second_conn_idx] == first_fdesc

        resume_close.set()
        close_thread.join(timeout=5)
        assert not close_thread.is_alive()
        assert not close_errors

        message = b"reconnected"
        second_client.sendall(message)
        assert server.receive(len(message), second_conn_idx) == message
    finally:
        resume_close.set()
        close_thread.join(timeout=5)
        first_client.close()
        second_client.close()
        server.close()


@skip_on_windows(reason="no real fd on windows")
def test_reconnect_while_closing_connection():
    process = multiprocessing.get_context("spawn").Process(
        target=_run_test_reconnect_while_closing_connection
    )
    process.start()
    try:
        process.join(timeout=30)
        assert not process.is_alive(), "Isolated socket test timed out"
    finally:
        if process.is_alive():
            process.kill()
            process.join()

    assert process.exitcode == 0
