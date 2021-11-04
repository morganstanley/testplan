.. raw:: html

  <div style="font-size:80px;font-family:Arial;font-weight:bold;">
    <i class="fa fa-check-square" style="color:green;padding-right:5px;"></i>
    Testplan
  </div>

a multi-testing framework
-------------------------

*..because unit tests can only go so far..*

Testplan is a `Python <http://python.org>`_ package that can start a local live
environment, setup mocks, connections to services and run tests against these.
It provides:

  * ``MultiTest`` a feature extensive functional testing system with a rich set
    of *assertions* and report rendering logic.
  * Built-in inheritable drivers to create a local live *environment*.
  * Configurable, diverse and expandable test execution mechanism including
    *parallel* execution capability.
  * Test *tagging* for flexible filtering and selective execution as well as
    generation of multiple reports (for each tag combination).
  * Integration with other unit testing frameworks (like GTest).
  * Rich, unified reports (json/PDF/XML) and soon (HTML/UI).


Basic example
=============

This is how a very basic Testplan application looks like.

.. code-block:: python

    import sys

    from testplan import test_plan
    from testplan.testing.multitest import MultiTest, testsuite, testcase


    def multiply(numA, numB):
        return numA * numB


    @testsuite
    class BasicSuite(object):

        @testcase
        def basic_multiply(self, env, result):
            result.equal(multiply(2, 3), 6, description='Passing assertion')
            result.equal(multiply(2, 2), 5, description='Failing assertion')


    @test_plan(name='Multiply')
    def main(plan):
        test = MultiTest(name='MultiplyTest',
                         suites=[BasicSuite()])
        plan.add(test)


    if __name__ == '__main__':
      sys.exit(not main())


Example execution:

.. code-block:: bash

    $ python ./test_plan.py -v
            Passing assertion - Pass
              6 == 6
            Failing assertion - Fail
              File: .../test_plan.py
              Line: 18
              4 == 5
          [basic_multiply] -> Fail
        [BasicSuite] -> Fail
      [MultiplyTest] -> Fail
    [Multiply] -> Fail


System integration testing example
==================================

Testing a server and a client communication.

.. code-block:: python

    import sys

    from testplan import test_plan
    from testplan.testing.multitest import MultiTest, testsuite, testcase
    from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient
    from testplan.common.utils.context import context


    @testsuite
    class TCPTestsuite(object):
        """Testsuite for server client connection testcases."""

        def setup(self, env):
            env.server.accept_connection()

        @testcase
        def send_and_receive_msg(self, env, result):
            """Basic send and receive hello message testcase."""
            msg = env.client.cfg.name
            result.log('Client is sending his name: {}'.format(msg))
            bytes_sent = env.client.send_text(msg)

            received = env.server.receive_text(size=bytes_sent)
            result.equal(received, msg, 'Server received client name')

            response = 'Hello {}'.format(received)
            result.log('Server is responding: {}'.format(response))
            bytes_sent = env.server.send_text(response)

            received = env.client.receive_text(size=bytes_sent)
            result.equal(received, response, 'Client received response')


    @test_plan(name='TCPConnections')
    def main(plan):
        test = MultiTest(name='TCPConnectionsTest',
                         suites=[TCPTestsuite()],
                         environment=[
                             TCPServer(name='server'),
                             TCPClient(name='client',
                                       host=context('server', '{{host}}'),
                                       port=context('server', '{{port}}'))])
        plan.add(test)


    if __name__ == '__main__':
        sys.exit(not main())


Example execution:

.. code-block:: bash

    $ python ./test_plan.py -v
            Client is sending: client
            Server received - Pass
              client == client
            Server is responding: Hello client
            Client received - Pass
              Hello client == Hello client
          [send_and_receive_msg] -> Pass
        [TCPTestsuite] -> Pass
      [TCPConnectionsTest] -> Pass
    [TCPConnections] -> Pass

A persistent and human readable test evidence PDF report:

.. code-block:: bash

    $ python ./test_plan.py --pdf report.pdf
      [TCPConnectionsTest] -> Pass
    [TCPConnections] -> Pass
    PDF generated at report.pdf

.. image:: ../images/pdf/readme_server_client.png

Contribution
============

A step by step guide on how to contribute to Testplan framework can be found
:ref:`here <contributing>`.

License
=======

License information `here <https://github.com/morganstanley/testplan/blob/main/LICENSE.md>`_.

.. toctree::
   :caption: Introduction
   :maxdepth: 2
   :hidden:

   introduction
   getting_started

.. toctree::
   :caption: Core
   :maxdepth: 2
   :hidden:

   unittests
   multitest
   drivers
   assertions
   output
   download/index
   api

.. toctree::
   :caption: Advanced
   :maxdepth: 2
   :hidden:

   interactive
   pools
   remote

.. toctree::
   :caption: Tools
   :maxdepth: 2
   :hidden:

   tpsreport

.. toctree::
   :caption: More Info
   :maxdepth: 2
   :hidden:
   
   design
   news
   about

