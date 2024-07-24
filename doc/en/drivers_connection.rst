Driver Connections
======

Connection between drivers can be visualised through the ``--driver-connection`` flag
in the cli. The connections are defined in the drivers' metadata. When the ``--driver-connection`` flag is enabled,
Testplan will read the drivers' metadata, extract their connections and format them into a flow chart
visible on the web report. The built-in drivers already have their connections defined and you can add
new connections by overriding the ``extract_driver_metadata`` method for each ``Driver`` subclass.

Testplan defines 2 types of connections by default, ``PortDriverConnection`` and ``FileDriverConnection``.

    * :py:class:`PortDriverConnection <testplan.testing.multitest.driver.connection.connection_info.PortDriverConnection>` defines
      connection between drivers via ports (e.g TCP, HTTP, FIX connections).

    * :py:class:`FileDriverConnection <testplan.testing.multitest.driver.connection.connection_info.FileDriverConnection>` defines
      connection between drivers via files (e.g Driver A writes to file X, Driver B reads file X).

Drivers that inherit `App` will automatically search for the its network and file connections via ``psutil`` functions.

New types of driver connections can also be defined. To do so, you will need to create 2 new classes that inherits
:py:class:`BaseConnectionInfo <testplan.testing.multitest.driver.connection.base.BaseConnectionInfo>` and 
:py:class:`BaseDriverConnection <testplan.testing.multitest.driver.connection.base.BaseDriverConnection>`.

Here is an example to define a new type of connection.

.. code-block:: python

    from testplan.testing.multitest.driver.connection import Direction, BaseConnectionInfo, BaseDriverConnection

    class NewConnectionInfo(BaseConnectionInfo):
        @property
        def connection_rep(self):
            return f"new://{self.identifier}" # this is the value by which drivers will be matched

        def promote_to_connection(self):
            return NewDriverConnection.from_connection_info(self)

    class NewDriverConnection(BaseDriverConnection):
        @classmethod
        def from_connection_info(cls, driver_connection_info: BaseConnectionInfo):
            # Add any custom logic if needed here.
            # For example, to add a dummy driver
            conn = super(NewDriverConnection, cls).from_connection_info(driver_connection_info)
            conn.drivers_listening["Dummy"].append("")
            return conn

        def add_driver_if_in_connection(self, driver_name: str, driver_connection_info: NewConnectionInfo):
            # Define any logic on how to match drivers here
            # Default behavior for predefined Connections is to match based on connection attribute
            if self.connection == driver_connection_info.connection:
                # Add the drivers here
                self.drivers_connecting[driver_name].append(SOME_INFO)
                return True
            return False

To use the new connection, override the ``extract_driver_metadata`` in the relevant ``Driver`` class.

.. code-block:: python

    from testplan.testing.multitest.driver.base import Driver, DriverMetadata, Direction

    class NewDriver(Driver):
        def extract_driver_metadata(self):
            return DriverMetadata(
                name=self.name,
                driver_metadata={
                    "class": self.__class__.__name__,
                },
                conn_info=[NewConnectionInfo(
                    name="Example",
                    service="Example",
                    protocol="Example",
                    identifier="Example",
                    direction=Direction.listening,
                )]
            )

