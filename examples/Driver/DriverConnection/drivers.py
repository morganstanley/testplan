from testplan.testing.multitest.driver.base import Driver, DriverMetadata
from testplan.testing.multitest.driver.app import App
from testplan.testing.multitest.driver.tcp import TCPClient
from testplan.testing.multitest.driver.connection import (
    Direction,
    PortConnectionInfo,
)

from custom_connection import CustomConnectionInfo


class CustomTCPClient(TCPClient):
    def extract_driver_metadata(self) -> DriverMetadata:
        return DriverMetadata(
            name=self.name,
            driver_metadata={"class": self.__class__.__name__},
            conn_info=[
                PortConnectionInfo(
                    name="Port",
                    service=self.SERVICE,
                    protocol=self.PROTOCOL,
                    identifier=self.identifier,
                    direction=self.DIRECTION,
                    local_port=self.local_port,
                    local_host=self.local_host,
                ),
                CustomConnectionInfo(
                    name="Custom",
                    service="Custom",
                    protocol="Custom",
                    identifier=0,
                    direction=Direction.CONNECTING,
                ),
            ],
        )


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
