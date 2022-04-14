"""
FIX messages parser.
"""
from enum import Enum


def tagsoverride(msg, override):
    """
    Merge in a series of tag overrides, with None
    signaling deletes of the original messages tags
    """
    for tag, value in override.items():
        if value is None:
            del msg[tag]
        else:
            msg[tag] = value
    return msg


class FixParser:
    """
    A barebones FIX parser
    """

    class State(Enum):
        """
        State enum for FixParser
        """

        NotStarted = 0
        ReadingHeader = 1
        ReadingLength = 2
        ReadingBody = 3
        ReadingCheckSum = 4

    def __init__(self):
        """
        Default constructor for FixParser
        """
        self.buffer = b""
        self.length_buffer = b""
        self.length = 0
        self.state = self.State.NotStarted

    def consume(self, buf):
        """
        Consume buf and return the number of bytes to read
        """
        if self.state == self.State.NotStarted:
            if buf == b"8" or buf == b"9":
                self.buffer += buf
                self.state = self.State.ReadingHeader
                return 1
            return 0
        elif self.state == self.State.ReadingHeader:
            self.buffer += buf
            if self.buffer[-3:] == b"\x019=" or self.buffer == b"9=":
                self.state = self.State.ReadingLength
            return 1
        elif self.state == self.State.ReadingLength:
            if buf == b"\x01":
                self.buffer += self.length_buffer + buf
                self.state = self.State.ReadingBody
                return int(self.length_buffer, 10)
            else:
                self.length_buffer += buf
                return 1
        elif self.state == self.State.ReadingBody:
            self.buffer += buf
            self.state = self.State.ReadingCheckSum
            return 7
        elif self.state == self.State.ReadingCheckSum:
            if not (buf.startswith(b"10=") and buf.endswith(b"\x01")):
                raise Exception('Incorrect checksum: "{}"'.format(buf))
            self.buffer += buf
            return 0
