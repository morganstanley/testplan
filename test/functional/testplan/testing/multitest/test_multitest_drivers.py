"""TODO."""

import os

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.common.entity.base import Environment, ResourceStatus
from testplan.common.utils.context import context
from testplan.common.utils.path import default_runpath
from testplan.common.utils.testing import log_propagation_disabled
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from testplan.logger import TESTPLAN_LOGGER



def runpath_maker(obj):
    """TODO."""
    return '{sep}tmp{sep}'.format(sep=os.sep)


@testsuite
class MySuite(object):

    @testcase
    def test_drivers(self, env, result):
        assert isinstance(env, Environment)
        assert isinstance(env.server, TCPServer)
        assert env.server.cfg.name == 'server'
        assert os.path.exists(env.server.runpath)
        assert isinstance(env.server.context, Environment)
        assert isinstance(env.client, TCPClient)
        assert env.client.cfg.name == 'client'
        assert os.path.exists(env.client.runpath)
        assert isinstance(env.client.context, Environment)
        assert env.server.context.client == env.client
        assert env.client.context.server == env.server
        assert env.server.status.tag == ResourceStatus.STARTED
        assert env.client.status.tag == ResourceStatus.STARTED

    @testcase
    def test_drivers_usage(self, env, result):
        """
        Client ---"Hello"---> Server ---"World"---> Client
        """
        env.server.accept_connection()
        msg = b'Hello'
        env.client.send(msg)
        # Server received data
        assert len(result.entries) == 0
        result.equal(env.server.receive(len(msg)), msg, 'Server received')
        assert len(result.entries) == 1
        assertion = result.entries[-1]
        assert bool(assertion) is True
        assert assertion.first == assertion.second == msg
        resp = b'World'
        env.server.send(resp)
        # Client received response
        result.equal(env.client.receive(len(resp)), resp, 'Client received')
        assert len(result.entries) == 2
        assertion = result.entries[-1]
        assert bool(assertion) is True
        assert assertion.first == assertion.second == resp

    @testcase
    def test_context_access(self, env, result):
        """
        Test context access from env and drivers.
        """
        assert isinstance(env, Environment)
        assert env.test_key == env['test_key'] == 'test_value'
        assert env is env.server.context
        assert env is env.client.context


def test_multitest_drivers():
    """TODO."""
    for idx, opts in enumerate(
          (dict(name='Mtest', suites=[MySuite()], runpath=runpath_maker),
           dict(name='Mtest', suites=[MySuite()]))):
        server = TCPServer(name='server')
        client = TCPClient(name='client',
                           host=context(server.cfg.name, '{{host}}'),
                           port=context(server.cfg.name, '{{port}}'))
        opts.update(environment=[server, client],
                    initial_context={'test_key': 'test_value'})
        mtest = MultiTest(**opts)
        assert server.status.tag == ResourceStatus.NONE
        assert client.status.tag == ResourceStatus.NONE
        mtest.run()
        res = mtest.result
        assert res.run is True
        if idx == 0:
            assert mtest.runpath == runpath_maker(None)
        else:
            assert mtest.runpath == default_runpath(mtest)
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status.tag == ResourceStatus.STOPPED
        assert client.status.tag == ResourceStatus.STOPPED


def test_multitest_drivers_in_testplan():
    """TODO."""
    for idx, opts in enumerate(
          (dict(name='MyPlan', parse_cmdline=False, runpath=runpath_maker),
           dict(name='MyPlan', parse_cmdline=False))):
        plan = Testplan(**opts)
        server = TCPServer(name='server')
        client = TCPClient(name='client',
                           host=context(server.cfg.name, '{{host}}'),
                           port=context(server.cfg.name, '{{port}}'))
        mtest = MultiTest(
            name='Mtest',
            suites=[MySuite()],
            environment=[server, client],
            initial_context={'test_key': 'test_value'})

        plan.add(mtest)
        assert server.status.tag == ResourceStatus.NONE
        assert client.status.tag == ResourceStatus.NONE

        with log_propagation_disabled(TESTPLAN_LOGGER):
            plan.run()

        res = plan.result
        assert res.run is True
        if idx == 0:
            assert plan.runpath == runpath_maker(None)
        else:
            assert plan.runpath == default_runpath(plan._runnable)
        assert mtest.runpath == os.path.join(plan.runpath, mtest.uid())
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status.tag == ResourceStatus.STOPPED
        assert client.status.tag == ResourceStatus.STOPPED
