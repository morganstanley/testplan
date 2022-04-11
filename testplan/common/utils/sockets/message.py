"""Server/Client communication message."""


class Message:
    """
    Message object with its codec to communicate data
    in a server/client connection.
    """

    def __init__(self, data=None, codec=None):
        """
        Create a new message.

        :param data: Message data content.
        :type data: ``str``
        :param codec: Codec object.
        :type codec: Subclass of
            :py:class:`Codec <testplan.common.utils.sockets.codec.Codec>`.
        """
        self.data = data
        self.codec = codec

    @classmethod
    def from_buffer(cls, data, codec):
        """Creates new message from buffer."""
        new = cls()
        new.codec = codec
        new.data = codec.parse(data)
        return new

    def to_buffer(self):
        """Serialize message data."""
        return self.codec.serialize(self.data)
