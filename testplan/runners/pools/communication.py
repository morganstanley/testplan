"""Communication protocol for execution pools."""
from typing import Dict


class Message:
    """Object to be used for pool-worker communication."""

    Ack = "Ack"
    TaskSending = "TaskSending"
    TaskResults = "TaskResults"
    TaskPullRequest = "TaskPullRequest"
    MetadataPull = "MetadataPull"
    Metadata = "Metadata"
    Stop = "Stop"
    Heartbeat = "Heartbeat"
    Message = "Message"
    ConfigRequest = "ConfigRequest"
    ConfigSending = "ConfigSending"
    SetupFailed = "SetupFailed"
    InitRequest = "InitRequest"
    KeepAlive = "KeepAlive"

    def __init__(self, **sender_metadata: Dict) -> None:
        """
        Create a new message object that contains sender information.

        :param sender_metadata: Useful key-value information by sender.
        """
        self.cmd = None
        self.data = None
        self.sender_metadata = sender_metadata

    def make(self, cmd: str, data: object = None) -> Message:
        """
        Crete a new message for communication.

        :param cmd: Command representing message purpose.
        :param data: Data of message object.
        :return: self
        """
        self.cmd = cmd
        self.data = data
        return self
