"""
Example for creating new custom connections
"""

from testplan.testing.multitest.driver.connection import (
    BaseConnectionInfo,
    BaseDriverConnection
)


class CustomConnectionInfo(BaseConnectionInfo):
    @property
    def connection_rep(self):
        # this is the value by which drivers will be matched
        return f"custom://{self.identifier}"

    def promote_to_connection(self):
        return CustomDriverConnection.from_connection_info(self)


class CustomDriverConnection(BaseDriverConnection):
    @classmethod
    def from_connection_info(cls, driver_connection_info: CustomConnectionInfo):
        # Add any custom logic here
        # For example, to add a dummy driver
        conn = super(CustomDriverConnection, cls).from_connection_info(
            driver_connection_info
        )
        conn.drivers_listening["Dummy Driver"].append("")
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
            self.drivers_connecting[driver_name].append("Read")
            return True
        return False