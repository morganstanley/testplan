from testplan.testing.multitest.driver.base import Driver
from testplan.testing.multitest.driver.app import App
from testplan.testing.multitest.driver.tcp import TCPClient
from testplan.testing.multitest.driver.connection import (
    Direction,
    Protocol,
    ConnectionExtractor,
)

from custom_connection import CustomConnectionExtractor


class CustomTCPClient(TCPClient):
    # override EXTRACTORS
    EXTRACTORS = [
        ConnectionExtractor(Protocol.TCP, Direction.CONNECTING),
        CustomConnectionExtractor(),
    ]


class WritingDriver(App):
    """
    Inherits the generic ``testplan.testing.multitest.driver.app.App`` driver
    and expose file path read from log extracts.
    """

    def __init__(self, **options):
        super(WritingDriver, self).__init__(**options)
        self.file_path = None

    def post_start(self):
        """
        Store file_path to be made available in its context
        so that reading driver can connect to it.
        """
        super(WritingDriver, self).post_start()
        self.file_path = self.extracts["file_path"]


class ReadingDriver(App):
    """
    Inherits the generic ``testplan.testing.multitest.driver.app.App`` driver
    """

    pass


class UnconnectedDriver(Driver):
    pass
