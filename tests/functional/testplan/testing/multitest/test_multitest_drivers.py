"""TODO."""

import os
import re
import getpass
import tempfile

from testplan.testing.filtering import Filter
from testplan.testing.ordering import NoopSorter

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan, defaults
from testplan.common.entity.base import Environment, ResourceStatus
from testplan.common.utils.context import context
from testplan.common.utils.path import StdFiles, default_runpath
from testplan.common.utils.testing import log_propagation_disabled
from testplan.testing.multitest.driver.base import Driver
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class MySuite(object):
    @testcase
    def test_drivers(self, env, result):
        assert isinstance(env, Environment)
        assert isinstance(env.server, TCPServer)
        assert env.server.cfg.name == "server"
        assert os.path.exists(env.server.runpath)
        assert isinstance(env.server.context, Environment)
        assert isinstance(env.client, TCPClient)
        assert env.client.cfg.name == "client"
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
        msg = b"Hello"
        env.client.send(msg)
        # Server received data
        assert len(result.entries) == 0
        result.equal(env.server.receive(len(msg)), msg, "Server received")
        assert len(result.entries) == 1
        assertion = result.entries[-1]
        assert bool(assertion) is True
        assert assertion.first == assertion.second == msg
        resp = b"World"
        env.server.send(resp)
        # Client received response
        result.equal(env.client.receive(len(resp)), resp, "Client received")
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
        assert env.test_key == env["test_key"] == "test_value"
        assert env is env.server.context
        assert env is env.client.context


def test_multitest_drivers(runpath):
    """TODO."""
    for idx, opts in enumerate(
        (
            dict(name="Mtest", suites=[MySuite()], runpath=runpath),
            dict(name="Mtest", suites=[MySuite()]),
        )
    ):
        server = TCPServer(name="server")
        client = TCPClient(
            name="client",
            host=context(server.cfg.name, "{{host}}"),
            port=context(server.cfg.name, "{{port}}"),
        )
        opts.update(
            environment=[server, client],
            initial_context={"test_key": "test_value"},
            stdout_style=defaults.STDOUT_STYLE,
            test_filter=Filter(),
            test_sorter=NoopSorter(),
        )
        mtest = MultiTest(**opts)
        assert server.status.tag == ResourceStatus.NONE
        assert client.status.tag == ResourceStatus.NONE
        mtest.run()
        res = mtest.result
        assert res.run is True
        if idx == 0:
            assert mtest.runpath == runpath
        else:
            assert mtest.runpath == default_runpath(mtest)
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status.tag == ResourceStatus.STOPPED
        assert client.status.tag == ResourceStatus.STOPPED


def test_multitest_drivers_in_testplan(runpath):
    """TODO."""
    for idx, opts in enumerate(
        (
            dict(name="MyPlan", parse_cmdline=False, runpath=runpath),
            dict(name="MyPlan", parse_cmdline=False),
        )
    ):
        plan = Testplan(**opts)
        server = TCPServer(name="server")
        client = TCPClient(
            name="client",
            host=context(server.cfg.name, "{{host}}"),
            port=context(server.cfg.name, "{{port}}"),
        )
        mtest = MultiTest(
            name="Mtest",
            suites=[MySuite()],
            environment=[server, client],
            initial_context={"test_key": "test_value"},
        )

        plan.add(mtest)
        assert server.status.tag == ResourceStatus.NONE
        assert client.status.tag == ResourceStatus.NONE

        with log_propagation_disabled(TESTPLAN_LOGGER):
            plan.run()

        res = plan.result
        assert res.run is True
        if idx == 0:
            assert plan.runpath == runpath
        else:
            assert plan.runpath == default_runpath(plan._runnable)
        assert mtest.runpath == os.path.join(plan.runpath, mtest.uid())
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status.tag == ResourceStatus.STOPPED
        assert client.status.tag == ResourceStatus.STOPPED


@testsuite
class EmptySuite(object):
    @testcase
    def test_empty(self, env, result):
        pass


class BaseDriver(Driver):
    """Base class of vulnerable driver which can raise exception."""

    @property
    def logpath(self):
        if self.cfg.logname:
            return os.path.join(self.runpath, self.cfg.logname)
        return self.outpath

    @property
    def outpath(self):
        return self.std.out_path

    @property
    def errpath(self):
        return self.std.err_path

    def starting(self):
        super(BaseDriver, self).starting()
        self.std = StdFiles(self.runpath)

    def stopping(self):
        super(BaseDriver, self).stopping()
        self.std.close()


class VulnerableDriver1(BaseDriver):
    """This driver raises exception during startup."""

    def starting(self):
        super(VulnerableDriver1, self).starting()
        self.std.err.write("Error found{}".format(os.linesep))
        self.std.err.flush()
        raise Exception("Startup error")


class VulnerableDriver2(BaseDriver):
    """This driver raises exception during shutdown."""

    def stopping(self):
        """Trigger driver stop."""
        super(VulnerableDriver2, self).stopping()
        with open(self.logpath, "w") as log_handle:
            for idx in range(1000):
                log_handle.write("This is line {}\n".format(idx))
        raise Exception("Shutdown error")


def test_multitest_driver_failure():
    """If driver fails to start or stop, the error log could be fetched."""
    plan1 = Testplan(name="MyPlan1", parse_cmdline=False)
    plan1.add(
        MultiTest(
            name="Mtest1",
            suites=[MySuite()],
            environment=[
                VulnerableDriver1(
                    name="vulnerable_driver_1", report_errors_from_logs=True
                )
            ],
        )
    )
    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan1.run()

    plan2 = Testplan(name="MyPlan2", parse_cmdline=False)
    plan2.add(
        MultiTest(
            name="Mtest2",
            suites=[MySuite()],
            environment=[
                VulnerableDriver2(
                    name="vulnerable_driver_2",
                    logname="logfile",
                    report_errors_from_logs=True,
                    error_logs_max_lines=10,
                )
            ],
        )
    )
    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan2.run()

    res1, res2 = plan1.result, plan2.result
    assert res1.run is True and res2.run is True

    report1, report2 = res1.report, res2.report
    assert "Exception: Startup error" in report1.entries[0].logs[0]["message"]
    assert "Exception: Shutdown error" in report2.entries[0].logs[0]["message"]

    text1 = report1.entries[0].logs[1]["message"].split(os.linesep)
    text2 = report2.entries[0].logs[1]["message"].split(os.linesep)
    assert re.match(r".*Information from log file:.+stderr.*", text1[0])
    assert re.match(r".*Error found.*", text1[1])
    assert re.match(r".*Information from log file:.+logfile.*", text2[0])
    for idx, line in enumerate(text2[1:]):
        assert re.match(r".*This is line 99{}.*".format(idx), line)
