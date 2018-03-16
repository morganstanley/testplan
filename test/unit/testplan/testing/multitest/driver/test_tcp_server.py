"""TODO."""

import os
import shutil

from testplan.common.entity.base import Environment
from testplan.common.utils.context import context
from testplan.common.utils.exceptions import should_raise
from testplan.common.utils.sockets import Message, Codec
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


def make_runpath(directory):
    return '{sep}var{sep}tmp{sep}{directory}'.format(sep=os.sep,
                                                     directory=directory)

def assert_obj_runpath(obj, runpath):
    assert obj.cfg.runpath in runpath
    assert obj.runpath is None
    assert obj._runpath is None
    with obj:
        assert obj.runpath == runpath
        assert obj._runpath == runpath
        assert os.path.exists(obj.runpath) is True


def test_basic_runpath():
    svr_path = make_runpath("srv_runpath")
    cli_path = make_runpath("cli_runpath")
    # Server runpath
    server = TCPServer(name='server', runpath=svr_path)
    assert_obj_runpath(server, svr_path)
    # Client runpath
    client = TCPClient(name='client', runpath=cli_path,
                       host=server._host,
                       port=server._port)
    assert_obj_runpath(client, cli_path)
    shutil.rmtree(svr_path, ignore_errors=True)
    shutil.rmtree(cli_path, ignore_errors=True)


def send_receive_message(server, client):
    """
    Client ---"Hello"---> Server ---"World"---> Client
    """
    msg_data = 'Hello'
    msg = Message(data=msg_data, codec=Codec())
    client.send(msg.to_buffer())
    server.accept_connection()
    recv = Message.from_buffer(data=server.receive(len(msg.data)),
                               codec=Codec())
    # Server received data
    assert recv.data == msg_data
    msg_data = 'World'
    resp = Message(data=msg_data, codec=Codec())
    server.send(resp.to_buffer())
    recv = Message.from_buffer(data=client.receive(len(resp.data)),
                               codec=Codec())
    # Client received response
    assert recv.data == msg_data


def test_send_receive_no_context():
    server = TCPServer(name='server',
                       host='localhost',
                       port=0)
    assert server.port is None
    server.start()
    server._wait_started()
    assert server.port != 0

    client = TCPClient(name='client',
                       host=server._host,
                       port=server._port)
    client.start()
    client._wait_started()

    send_receive_message(server, client)
    client.stop()
    client._wait_stopped()
    server.stop()
    server._wait_stopped()


def test_send_receive_with_none_context():
    server = TCPServer(name='server',
                       host='localhost',
                       port=0)

    client = TCPClient(name='client',
                       host=context('server', '{{host}}'),
                       port=context('server', '{{port}}'))
    assert server.port is None
    server.start()
    server._wait_started()
    assert server.port != 0
    should_raise(ValueError, client.start)
    server.stop()
    server._wait_stopped()


def test_send_receive_with_context():
    rcxt = Environment()

    server = TCPServer(name='server',
                       host='localhost',
                       port=0)
    rcxt.add(server)

    client = TCPClient(name='client',
                       host=context('server', '{{host}}'),
                       port=context('server', '{{port}}'))
    rcxt.add(client)

    assert server.port is None
    for item in rcxt:
        item.start()
        item._wait_started()
        assert item.port != 0

    send_receive_message(server, client)
    for item in reversed(list(rcxt)):
        item.stop()
        item._wait_stopped()
