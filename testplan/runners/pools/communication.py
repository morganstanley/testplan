"""Communication protocol for execution pools."""

from typing import Any, Optional


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
    DiscardPending = "DiscardPending"
    InitRequest = "InitRequest"
    KeepAlive = "KeepAlive"

    def __init__(self, **sender_metadata: Any) -> None:
        """
        Create a new message object that contains sender information.

        :param sender_metadata: Useful key-value information by sender.
        """
        self.cmd: Optional[str] = None
        self.data: Any = None
        self.sender_metadata: dict[str, Any] = sender_metadata

    def make(self, cmd: str, data: object = None) -> "Message":  # type: ignore[valid-type]
        """
        Crete a new message for communication.

        :param cmd: Command representing message purpose.
        :param data: Data of message object.
        :return: self
        """
        self.cmd = cmd
        self.data = data
        return self
