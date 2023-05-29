Drivers
*******

Introduction
============

Drivers are easy-to-use Testplan-provided interfaces for interacting with
outside applications and services during testing runtime. With the help of
drivers, users can easily control related applications in the scenario of
integration testing.

Drivers can be used in Testplan MultiTest as well as Testplan-provided unit
test framework integrations. Below is an concrete example of how drivers can
be used in Testplan MultiTest.

.. code-block:: python

    # Example environment of three dynamically connecting drivers.
    #  --------------         -----------------         ---------------
    #  |            | ------> |               | ------> |             |
    #  |   Client   |         |  Application  |         |   Service   |
    #  |            | <------ |               | <------ |             |
    #  --------------         -----------------         ---------------

    ...  # Other arguments passed to MultiTest constructor
    environment=[
        Service(name='service'),
        Application(name='app',
                    host=context('service', '{{host}}'),
                    port=context('service', '{{port}}')),
        Client(name='client',
               host=context('app', '{{host}}'),
               port=context('app', '{{port}}'))
    ],
    ...  # Other arguments passed to MultiTest constructor

Testplan provides a dynamic driver configuration system, around the two
following properties:

    * Drivers can be configured with attributes of other drivers.
    * Driver configuration is not required to exist until the driver starts.


Context and Context Value
=========================

In Testplan, drivers can retrieve attributes of others from the Context.
Context is basically the environment which the driver belongs to, where a group
of drivers serve together for the integration test. Since certain driver
configuration does not exist until that driver has successfully started, Context
Value are created as late-bound values which will be resolved during driver
start-up, from the context, to actual configuration values.

A context value in Python code is created from a
:py:func:`context() <testplan.common.utils.context.context>` call, taking a
driver name and a `Jinja2 <https://jinja.palletsprojects.com/en/3.1.x/templates/>`_
expression that must be a valid attribute of the corresponding driver. A context
value can also be used in the configuration file of a driver with the syntax of
``{{context["<driver_name>"].<attribute_name>}}`` in the place of configuration
value. The configuration file will be processed with Jinja2 template engine
during driver start-up, thus it must be a valid Jinja2 template.

In practice, context values are often used for communicating hostnames, port
numbers, file paths, and other such values dynamically generated at runtime
among drivers. With the usage of context values, we can easily avoid collisions
between setups being shared among various testing scenarios. As you might
already noticed, the Application driver in the above example is using context
values to retrieve the host and port of the Service driver to connect to, so
does that Client driver.

Start-up schedule
=================

In the above example, we can easily find out that the Application driver cannot
actually enter the start-up procedure until the Service driver has fully
started, so the Application must come after the Service, and the Client must
come after the Application. Testplan provides three ways to specify the start-up
schedule of the drivers:

    * Pass a list of drivers to the ``environment`` parameter. In this case,
      drivers will be scheduled sequentially. The driver comes later in the
      passed-in list will not be started until the earlier one has fully started.

    * Pass a list of drivers to the ``environment`` parameter, while some of them
      has ``async_start`` parameter set to ``True``. This case is similar to the
      previous one except that drivers after such an ``async_start`` driver will
      be scheduled to start even that driver has not fully started.

    * Pass a list of drivers to the ``environment`` parameter, and pass a
      dictionary to the ``dependencies`` parameter. In this case, Testplan will
      work out a feasible schedule meeting all the dependency (driver A must start
      before driver B) requirements while tend to start more drivers
      simultaneously, and the order of drivers in ``environment`` list will be
      ignored. For a key-value pair in the ``dependencies`` dictionary, the
      drivers on the key side should always be fully started before scheduling the
      drivers on the value side, i.e. left-hand side are before right-hand side.

The third way (making use of ``dependencies`` parameter) is usually recommended
since the overall test runtime could be possibly reduced with drivers being
started simultaneously. The above example can be changed as following using
``dependencies``:

.. code-block:: python

    # Example environment of three dynamically connecting drivers.
    #  --------------         -----------------         ---------------
    #  |            | ------> |               | ------> |             |
    #  |   Client   |         |  Application  |         |   Service   |
    #  |            | <------ |               | <------ |             |
    #  --------------         -----------------         ---------------

    # Outside MultiTest constructor
    client = Client(name='client',
                    host=context('app', '{{host}}'),
                    port=context('app', '{{port}}'))
    application = Application(name='app',
                              host=context('service', '{{host}}'),
                              port=context('service', '{{port}}'))
    service = Service(name='service')
    # Outside MultiTest constructor

    # Inside MultiTest constructor
    ...  # Other arguments passed to MultiTest constructor
    environment=[
        client, application, service  # Order no longer matters
    ],
    dependencies={
        service: application,
        application: client
    },
    ...  # Other arguments passed to MultiTest constructor
    # Inside MultiTest constructor

Another example containing simultaneous driver start-up can be found
:ref:`here <example_driver_dependency>`.

Work with unit test
===================

Drivers can also be useful while working with other unit testing frameworks like
like GTest or Hobbes Test. Testplan will export environment variables for newly
started test process. Have a look at the following code:

.. code-block:: python

    plan.add(GTest(
        name='My GTest',
        binary=BINARY_PATH,
        environment=[
            TCPServer(name='my server'),
            TCPClient(name='client-101',
                host=context('server', '{{host}}'),
                port=context('server', '{{port}}')
            )
        ]
    )

In your unit test process, you can find an environment variable named
``DRIVER_MY_SERVER_ATTR_HOST``, likewise, ``DRIVER_CLIENT_101_ATTR_PORT`` is also
available. It is easy to understand that the string is formatted in uppercase,
like ``DRIVER_<uid of driver>_ATTR_<attribute name>``, while hyphens and spaces
are replaced by underscores.
