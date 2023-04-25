.. _custom_driver:

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

Here is a custom driver that inherits the built-in
:py:class:`App <testplan.testing.multitest.driver.app.App>` driver and overwrites
:py:meth:`App.post_start <testplan.testing.multitest.driver.app.App.post_start>`
method to expose ``host`` and ``port`` attributes that was written in the
logfile by the application binary.

.. code-block:: python

    from testplan.testing.multitest.driver.app import App

    class ServerApp(App):

        def __init__(self, **options):
            super(ServerApp, self).__init__(**options)
            self.host = None
            self.port = None

        def post_start(self):
            super(ServerApp, self).post_start()
            # In this example, log_regexps contain:
            #     re.compile(r'.*Listener on: (?P<listen_address>.*)')
            # and the logfile will contain a line like:
            #     Listener on: 127.0.0.1:10000
            self.host, self.port = self.extracts['listen_address'].split(':')
            # so self.host value will be: '127.0.0.1'
            # and self.port value will be: '10000'

See also the full
:ref:`downloadable example <example_fxconverter>` for this custom app.
