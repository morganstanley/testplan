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
