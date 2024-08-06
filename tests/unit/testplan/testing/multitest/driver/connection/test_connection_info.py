"""Unit tests for the connections."""
import pytest

from testplan.testing.multitest.driver.connection import (
    Direction,
    Protocol,
    PortConnectionInfo,
    PortDriverConnectionGroup,
)


class TestPortDriverConnection:
    connecting_to_0_from_0 = PortConnectionInfo(
        name="connection 1",
        service=Protocol.TCP,
        protocol=Protocol.TCP,
        identifier=0,
        direction=Direction.CONNECTING,
        port=0,
    )
    connecting_to_0_from_1 = PortConnectionInfo(
        name="connection 2",
        service=Protocol.TCP,
        protocol=Protocol.TCP,
        identifier=0,
        direction=Direction.CONNECTING,
        port=1,
    )
    listening_from_0 = PortConnectionInfo(
        name="connection 3",
        service=Protocol.TCP,
        protocol=Protocol.TCP,
        identifier=0,
        direction=Direction.LISTENING,
        port=0,
    )
    connecting_to_1 = PortConnectionInfo(
        name="connection 4",
        service=Protocol.TCP,
        protocol=Protocol.TCP,
        identifier=1,
        direction=Direction.CONNECTING,
        port=0,
    )
    connecting_to_0_from_1_with_FIX = PortConnectionInfo(
        name="connection 5",
        service="FIX",
        protocol=Protocol.TCP,
        identifier=0,
        direction=Direction.CONNECTING,
        port=1,
    )

    def test_does_not_add_if_not_in_connection(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        assert not connection.add_driver_if_in_connection(
            "driver", self.connecting_to_1
        )
        assert len(connection.drivers_connecting) == 0

    def test_add_if_in_connection(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        assert connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        assert len(connection.drivers_connecting) == 1
        assert connection.drivers_connecting["driver"] == ["0"]

    def test_no_duplicat_port_if_already_in_connection(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        assert len(connection.drivers_connecting) == 1
        assert connection.drivers_connecting["driver"] == ["0"]

    def test_add_multiple_port_if_driver_already_in_connection(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_1
        )
        assert len(connection.drivers_connecting) == 1
        assert connection.drivers_connecting["driver"] == ["0", "1"]

    def test_update_service_if_not_in_protocol(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_1_with_FIX
        )
        assert connection.service == "FIX"
        assert len(connection.drivers_connecting) == 1
        assert connection.drivers_connecting["driver"] == ["0", "1"]

    def test_should_include_if_both_connecting_and_listening(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        connection.add_driver_if_in_connection("driver", self.listening_from_0)
        assert connection.should_include()
        assert len(connection.drivers_connecting) == 1
        assert len(connection.drivers_listening) == 1
        assert connection.drivers_connecting["driver"] == ["0"]
        assert connection.drivers_listening["driver"] == ["0"]

    def test_should_not_include_if_missing_connecting_or_listening(self):
        connection = PortDriverConnectionGroup.from_connection_info(
            self.connecting_to_0_from_0
        )
        assert not connection.should_include()

        connection.add_driver_if_in_connection(
            "driver", self.connecting_to_0_from_0
        )
        assert not connection.should_include()

        connection = PortDriverConnectionGroup.from_connection_info(
            self.listening_from_0
        )
        connection.add_driver_if_in_connection("driver", self.listening_from_0)
        assert not connection.should_include()
