"""Communication protocol for execution pools."""


class Message(object):
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

    def __init__(self, **sender_metadata):
        """
        Create a new message object that contains sender information.

        :param sender_metadata: Useful key-value information by sender.
        :type sender_metadata: ``dict``
        """
        self.cmd = None
        self.data = None
        self.sender_metadata = sender_metadata

    def make(self, cmd, data=None):
        """
        Crete a new message for communication.

        :param cmd: Command representing message purpose.
        :param cmd: ``str``
        :param data: Data of message object.
        :param data: ``object``
        :return: self
        :rtype: :py:class:`~testplan.runners.pools.communication.Message`
        """
        self.cmd = cmd
        self.data = data
        return self
