Driver Connections
======

Connection between drivers can be visualised through the ``--driver-info`` flag
in the cli. The connections are defined in the drivers' metadata. When the ``--driver-info`` flag is enabled,
Testplan will extract connections from each driver and format them into a flow chart
visible on the web report. The built-in drivers already have their connections defined and you can add
new connections by overriding the ``EXTRACTORS`` attribute for each ``Driver`` subclass.

Testplan defines 2 types of connections by default, ``PortDriverConnection`` and ``FileDriverConnection``.

    * :py:class:`PortDriverConnection <testplan.testing.multitest.driver.connection.connection_info.PortDriverConnection>` defines
      connection between drivers via ports (e.g TCP, HTTP, FIX connections).

    * :py:class:`FileDriverConnection <testplan.testing.multitest.driver.connection.connection_info.FileDriverConnection>` defines
      connection between drivers via files (e.g Driver A writes to file X, Driver B reads file X).

Drivers that inherit `App` will automatically search for the its network and file connections
via the ``SubprocessPortConnectionExtractor`` and the ``SubprocessFileConnectionExtractor``. These extractors use ``psutil`` functions to extract connections.

New types of driver connections can also be defined. To do so, you will need to create 3 new classes that inherits
:py:class:`BaseConnectionInfo <testplan.testing.multitest.driver.connection.base.BaseConnectionInfo>`, 
:py:class:`BaseDriverConnectionGroup <testplan.testing.multitest.driver.connection.base.BaseDriverConnectionGroup>` and
:py:class:`BaseConnectionExtractor <testplan.testing.multitest.driver.connection.base.BaseConnectionExtractor>`.

Here is an example to define a new type of connection.

.. code-block:: python

    from testplan.testing.multitest.driver.connection import Direction, BaseConnectionInfo, BaseDriverConnectionGroup

    class NewConnectionInfo(BaseConnectionInfo):
        @property
        def connection_rep(self):
            return f"new://{self.identifier}" # this is the value by which drivers will be matched

        def promote_to_connection(self):
            return NewDriverConnectionGroup.from_connection_info(self)

    class NewDriverConnectionGroup(BaseDriverConnectionGroup):
        @classmethod
        def from_connection_info(cls, driver_connection_info: BaseConnectionInfo):
            # Add any custom logic if needed here.
            # For example, to add a dummy driver
            conn = super(NewDriverConnection, cls).from_connection_info(driver_connection_info)
            conn.in_drivers["Dummy"].add("")
            return conn

        def add_driver_if_in_connection(self, driver_name: str, driver_connection_info: NewConnectionInfo):
            # Define any logic on how to match drivers here
            # Default behavior for predefined Connections is to match based on connection attribute
            if self.connection == driver_connection_info.connection:
                # Add the drivers here
                self.out_drivers[driver_name].append(SOME_INFO)
                return True
            return False

    class NewConnectionExtractor(BaseConnectionExtractor):
        def extract_connections(self, driver):
            return [
                NewConnectionInfo(
                    name="Example",
                    service="Example",
                    protocol="Example",
                    identifier=driver.attribute,
                    direction=Direction.LISTENING,
                )
            ]

To use the new connection, override ``EXTRACTORS`` in the relevant ``Driver`` class.

.. code-block:: python

    from testplan.testing.multitest.driver.base import Driver, DriverMetadata, Direction

    class NewDriver(Driver):
        EXTRACTORS = [NewConnectionExtractor()]

See the example for more information :ref:`here <example_driver_connection>`.