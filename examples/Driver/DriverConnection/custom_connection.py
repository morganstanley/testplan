"""
Example for creating new custom connections
"""

from typing import List
from testplan.testing.multitest.driver.connection import (
    BaseConnectionInfo,
    BaseDriverConnectionGroup,
    BaseConnectionExtractor,
    Direction,
)


class CustomConnectionInfo(BaseConnectionInfo):
    @property
    def connection_rep(self):
        # this is the value by which drivers will be matched
        # by default, this is f"self.protocol}//{self.identifier}
        return f"custom://{self.identifier}"

    def promote_to_connection(self):
        return CustomDriverConnectionGroup.from_connection_info(self)


class CustomDriverConnectionGroup(BaseDriverConnectionGroup):
    @classmethod
    def from_connection_info(
        cls, driver_connection_info: CustomConnectionInfo
    ):
        # Add any custom logic here
        # For example, to add a dummy driver
        conn = super(CustomDriverConnectionGroup, cls).from_connection_info(
            driver_connection_info
        )
        conn.in_drivers["Dummy Driver"].add("")
        return conn

    def add_driver_if_in_connection(
        self, driver_name: str, driver_connection_info: CustomConnectionInfo
    ):
        # Define logic on how to match drivers here
        # Default behavior for predefined connections is to match based on the connection_rep
        if self.connection_rep == driver_connection_info.connection_rep:
            # Append the identifier
            # For port based connection, ports are the identifier
            # For file based connections, read/write are the identifier
            self.out_drivers[driver_name].add("Read")
            return True
        return False


class CustomConnectionExtractor(BaseConnectionExtractor):
    def extract_connection(self, driver) -> List[CustomConnectionInfo]:
        return [
            CustomConnectionInfo(
                protocol="custom",
                identifier=driver.name,
                direction=Direction.CONNECTING,
            )
        ]
