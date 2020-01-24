"""TODO."""

from testplan.common.utils.sockets import Message
from testplan.common.utils.sockets import Codec


def test_basic_message():
    codec = Codec()
    buff = b"Hello world"
    assert isinstance(buff, bytes)
    message = Message.from_buffer(buff, codec)
    assert isinstance(message, Message)
    assert isinstance(message.data, str)
    assert isinstance(message.codec, Codec)
    assert b"Hello world" == message.to_buffer()
