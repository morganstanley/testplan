"""Codec utils."""


class Codec:
    """Codec to serialize/deserialize a message."""

    def parse(self, buffer):
        """Creates a string message from buffer."""
        return str(buffer.decode("utf-8"))

    def serialize(self, msg):
        """Serialize string message to bytes."""
        return bytes(msg.encode("utf-8"))
