.. _multitest_drivers:

Drivers
*******

MultiTest provides a dynamic driver configuration system, around the two
following properties:

    * Drivers can depend on other drivers.
    * Driver configuration is not required to exist until the driver starts.

Dependencies between drivers are expressed very simply: any driver in the
environment list passed to MultiTest is allowed to depend on any other driver
appearing earlier than itself in the list.

Specifying dependencies this way is sufficiently flexible to cover all cases
while remaining simple enough to understand and easily express.

Dependent values can be created either through the
:py:func:`context() <testplan.common.utils.context.context>` call, or using
pairs of double curly brackets in configuration files (MultiTest is using the
`Tempita <http://pythonpaste.org/tempita/>`_ templating library).

.. code-block:: python

    # Example environment of three dynamically connecting drivers.
    #  --------------         -----------------         ---------------
    #  |            | ------> |               | ------> |             |
    #  |   Client   |         |  Application  |         |   Service   |
    #  |            | <------ |               | <------ |             |
    #  --------------         -----------------         ---------------

    environment=[
        Service(name='service'),
        Application(name='app',
                    host=context('service', '{{host}}')
                    port=context('service', '{{port}}'))
        Client(name='client',
               host=context('app', '{{host}}')
               port=context('app', '{{port}}'))
    ]


Configuration
=============

Context
=======
Context at any point during the MultiTest startup is defined as the state of the
set of drivers that have already started. As soon as a driver has completed its
start step successfully, all of its attributes become part of the context and
are thus made available to all drivers that will start after it.

In practice the context is often used to communicate hostnames, port values,
file paths, and other such values dynamically generated at runtime to avoid
collisions between setups that must be shared between the various drivers to
communicate meaningfully.

Any context value from any process can be accessed by the
:py:func:`context() <testplan.common.utils.context.context>` call, taking a
driver name and a tempita expression that must be valid on that driver name.
This call effectively creates a late-bound value that drivers will resolve at
startup, against the current context.

Those expressions can also be used in the configuration of the drivers that
support them, for example
:py:class:`App <testplan.testing.multitest.driver.app.App>`. In the case of
configurations, the values of the driver that is being configured are available
in the global scope, and other drivers can be accessed through the special
'context' object.

Network dependencies
====================
Probably one of the most common use-cases of the context is the passing of
network addresses between processes. For robustness reasons, it is much
preferable to neither hardcode hosts nor ports in test setups. Ports can
typically be assigned by the operating system in such a way that collisions
between instances are avoided.

This is a simple example of a server and a client, where the server is binding
to ``localhost:0`` and communicating at runtime to the client where it is in
fact listening. As long as there are dynamic ports available on the host, this
setup will start reliably and will not collide with other already running
applications.

.. code-block:: python

    # Example environment of a Server and 2 Clients.
    #
    #      +--------- client1
    #      |
    #   server
    #      |
    #      +--------- client2
    #
    # Client will have access to the server host, port
    # after server starts.

    [
        TCPServer('server'),
        TCPClient(
            'client1',
            context('server', '{{host}}'),
            context('server', '{{port}}')
        )
        TCPClient(
            'client2',
            context('server', '{{host}}'),
            context('server', '{{port}}')
        )
    ]

Users are strongly encouraged to follow this practice rather than hardcode host
names and port numbers in their test setups.

Work with unit test
===================

Drivers can also be useful while working with other unit testing frameworks like
like GTest or Hobbes Test. Testplan will export environment variables for newly
started test process. Have a look at the following code:

.. code-block:: python

    plan.add(GTest(
        name='My GTest',
        driver=BINARY_PATH,
        environment=[
            TCPServer(name='my server'),
            TCPClient(name='client-101',
                host=context('server', '{{host}}'),
                port=context('server', '{{port}}')
            )
        ]
    )

In your unit test process, you can find an environment variable named
'DRIVER_MY_SERVER_ATTR_HOST', likewise, 'DRIVER_CLIENT_101_ATTR_PORT' is also
available. It is easy to understand that the string is formatted in uppercase,
like 'DRIVER_<uid of driver>_ATTR_<attribute name>', while hyphens and spaces
are replaced by underscores.

.. _multitest_builtin_drivers:

Built-in drivers
================

    * :py:class:`Driver <testplan.testing.multitest.driver.base.Driver>` baseclass
      which provides the most common functionality features and all other
      drivers inherit .

    * :py:class:`App <testplan.testing.multitest.driver.app.App>` that handles
      application binaries. See an example demonstrating how App driver
      can be used on an fxconverter python application
      :ref:`here <example_fxconverter>`.

    * :py:class:`TCPServer <testplan.testing.multitest.driver.tcp.server.TCPServer>` and
      :py:class:`TCPClient <testplan.testing.multitest.driver.tcp.client.TCPClient>` to
      create TCP connections on the Multitest local environment and can often
      used to mock services. See some examples :ref:`here <example_tcp>`.

    * :py:class:`ZMQServer <testplan.testing.multitest.driver.zmq.server.ZMQServer>` and
      :py:class:`ZMQClient <testplan.testing.multitest.driver.zmq.client.ZMQClient>` to
      create ZMQ connections on the Multitest local environment.
      See some examples demonstrating PAIR and PUB/SUB connections
      :ref:`here <example_zmq>`.

    * :py:class:`FixServer <testplan.testing.multitest.driver.fix.server.FixServer>` and
      :py:class:`FixClient <testplan.testing.multitest.driver.fix.client.FixClient>` to
      enable FIX protocol communication i.e between trading applications and
      exchanges.
      See some examples demonstrating FIX communication :ref:`here <example_fix>`.

    * :py:class:`HTTPServer <testplan.testing.multitest.driver.http.server.HTTPServer>` and
      :py:class:`HTTPClient <testplan.testing.multitest.driver.http.client.HTTPClient>` to
      enable HTTP communication.
      See some examples demonstrating HTTP communication :ref:`here <example_http>`.

    * :py:class:`Sqlite3 <testplan.testing.multitest.driver.sqlite.Sqlite3>`
      to connect to a database and perform sql queries etc. Examples can be
      found :ref:`here <example_sqlite3>`.

.. _multitest_custom_drivers:

Custom
======

New drivers can be created to drive custom applications and services,
manage database connections, represent mocks etc. These can inherit existing
ones (or the base :py:class:`Driver <testplan.testing.multitest.driver.base.Driver>`)
and customize some of its methods i.e (``__init__``, ``starting``, ``stopping``,
etc).
The :py:class:`~testplan.testing.multitest.driver.base.Driver` base class
contains most common functionality that a MultiTest environment driver requires,
including ability to provide file templates that will be instantiated using
the context information on runtime and mechanisms to extract values from
logfiles to retrieve dynamic values assigned (like host/port listening).

A generic :py:class:`Application <testplan.testing.multitest.driver.app.App>`
driver inherits the base driver class and extends it with logic to start/stop
a binary as a sub-process.

Here is a custom driver inherits the built-in
:py:class:`App <testplan.testing.multitest.driver.app.App>` driver and overwrites
:py:meth:`App.started_check <testplan.testing.multitest.driver.app.App.started_check>`
method to expose ``host`` and ``port`` attributes that was written in the
logfile by the application binary.

.. code-block:: python

    from testplan.testing.multitest.driver.app import App

    class ServerApp(App):

        def __init__(self, **options):
            super(ServerApp, self).__init__(**options)
            self.host = None
            self.port = None

        def started_check(self, timeout=None):
            super(ServerApp, self).started_check(timeout=timeout)
            # In this example, log_regexps contain:
            #     re.compile(r'.*Listener on: (?P<listen_address>.*)')
            # and the logfile will contain a line like:
            #     Listener on: 127.0.0.1:10000
            self.host, self.port = self.extracts['listen_address'].split(':')
            # so self.host value will be: '127.0.0.1'
            # and self.port value will be: '10000'

See also the full
:ref:`downloadable example <example_fxconverter>` for this custom app.
