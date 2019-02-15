from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from my_tests.basic import BasicSuite
from my_tests.tcp import TCPSuite


def make_multitest(idx=''):
    def accept_connection(env):
        env.server.accept_connection()

    return MultiTest(
        name='Test{}'.format(idx),
        suites=[BasicSuite(), TCPSuite()],
        environment=[
            TCPServer(name='server'),
            TCPClient(name='client',
                      host=context('server', '{{host}}'),
                      port=context('server', '{{port}}'))],
        after_start=accept_connection)
