"""TODO."""

import os
import re
import time


from testplan.testing.filtering import Filter
from testplan.testing.multitest.base import RuntimeEnvironment
from testplan.testing.ordering import NoopSorter

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock, defaults
from testplan.common.entity.base import Environment, ResourceStatus
from testplan.common.utils.context import context
from testplan.common.utils.path import StdFiles, default_runpath
from testplan.common.utils.strings import slugify
from testplan.common.utils.timing import TimeoutException
from testplan.testing.multitest.driver.base import Driver
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient


@testsuite
class MySuite:
    @testcase
    def test_drivers(self, env, result):
        assert isinstance(env, RuntimeEnvironment)
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
        assert env.server.status == ResourceStatus.STARTED
        assert env.client.status == ResourceStatus.STARTED

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
        assert isinstance(env, RuntimeEnvironment)
        assert env.test_key == env["test_key"] == "test_value"
        assert env._environment is env.server.context
        assert env._environment is env.client.context

    @testcase
    def test_env_iterable(self, env, result):
        assert [driver.name for driver in env] == ["server", "client"]

    @testcase
    def test_env_is_container_like(self, env, result):
        for driver in ["server", "client"]:
            assert driver in env


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
        assert server.status == ResourceStatus.NONE
        assert client.status == ResourceStatus.NONE
        res = mtest.run()
        assert res.run is True
        assert res.report.passed
        if idx == 0:
            assert mtest.runpath == runpath
        else:
            assert mtest.runpath == default_runpath(mtest)
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status == ResourceStatus.STOPPED
        assert client.status == ResourceStatus.STOPPED


def test_multitest_drivers_in_testplan(runpath):
    """TODO."""
    for idx, opts in enumerate(
        (dict(name="MyPlan", runpath=runpath), dict(name="MyPlan"))
    ):
        plan = TestplanMock(**opts)
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
        assert server.status == ResourceStatus.NONE
        assert client.status == ResourceStatus.NONE

        plan.run()
        res = plan.result

        assert res.run is True
        assert res.report.passed
        if idx == 0:
            assert plan.runpath == runpath
        assert mtest.runpath == os.path.join(
            plan.runpath, slugify(mtest.uid())
        )
        assert server.runpath == os.path.join(mtest.runpath, server.uid())
        assert client.runpath == os.path.join(mtest.runpath, client.uid())
        assert server.status == ResourceStatus.STOPPED
        assert client.status == ResourceStatus.STOPPED


@testsuite
class EmptySuite:
    @testcase
    def test_empty(self, env, result):
        pass


class BaseDriver(Driver):
    """Base class of vulnerable driver which can raise exception."""

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
        self.std.err.write("Error found\n")
        self.std.err.flush()
        raise Exception("Startup error")


class VulnerableDriver2(BaseDriver):
    """This driver raises exception during shutdown."""

    def stopping(self):
        """Trigger driver stop."""
        super(VulnerableDriver2, self).stopping()
        with open(self.logpath, "a") as log_handle:
            for idx in range(1000):
                log_handle.write(f"This is line {idx}\n")
        raise Exception("Shutdown error")


class GoodDriver(BaseDriver):
    """This driver timeout during start."""

    def starting(self):
        super(GoodDriver, self).starting()
        time.sleep(2)
        self.std.out.write("GoodDriver started")
        self.std.out.flush()


def test_multitest_driver_startup_failure(mockplan):
    """If driver fails to start or stop, the error log could be fetched."""
    mockplan.add(
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
    mockplan.run()

    res = mockplan.result
    assert res.run is True
    report = res.report

    assert "Exception: Startup error" in report.entries[0].logs[0]["message"]
    text = report.entries[0].logs[1]["message"].split(os.linesep)
    assert re.match(r".*Information from log file:.+stderr.*", text[0])
    assert re.match(r".*Error found.*", text[1])


def test_multitest_driver_fetch_error_log(mockplan):
    """
    If driver fails to start or stop, the specified tailing lines in error log
    could be fetched.
    """

    mockplan.add(
        MultiTest(
            name="Mtest2",
            suites=[MySuite()],
            environment=[
                VulnerableDriver2(
                    name="vulnerable_driver_2",
                    report_errors_from_logs=True,
                    error_logs_max_lines=10,
                )
            ],
        )
    )
    mockplan.run()

    res = mockplan.result
    assert res.run is True

    report = res.report
    assert "Exception: Shutdown error" in report.entries[0].logs[0]["message"]

    text = report.entries[0].logs[1]["message"].split(os.linesep)
    assert re.match(r".*Information from log file:.+stdout.*", text[0])
    for idx, line in enumerate(text[1:]):
        assert re.match(r".*This is line 99{}.*".format(idx), line)


def test_multitest_driver_start_timeout():

    driver1 = BaseDriver(
        name="timeout_driver",
        timeout=1,
        stdout_regexps=[re.compile(r"Expression that won't match")],
    )
    assert driver1.cfg.status_wait_timeout == 1
    assert driver1.cfg.timeout == 1

    try:
        with driver1:
            # we will not reach here
            assert False
    except TimeoutException as exc:
        assert "Timeout after 1 seconds" in str(exc)

    driver2 = GoodDriver(
        name="good_driver",
        timeout=1,  # Note: this timeout does not include time spent in starting
        stdout_regexps=[re.compile("GoodDriver started")],
    )

    with driver2:
        assert True


def pre_start_fn(driver):
    assert driver.pre_start_cnt > 0
    driver.pre_start_fn_cnt += 1


def post_start_fn(driver):
    assert driver.post_start_cnt > 0
    driver.post_start_fn_cnt += 1


def pre_stop_fn(driver):
    assert driver.pre_stop_cnt > 0
    driver.pre_stop_fn_cnt += 1


def post_stop_fn(driver):
    assert driver.post_stop_cnt > 0
    driver.post_stop_fn_cnt += 1


class CustomDriver(Driver):
    """A driver which can count how many times its method is called."""

    def __init__(self, **options):
        super(CustomDriver, self).__init__(
            pre_start=pre_start_fn,
            post_start=post_start_fn,
            pre_stop=pre_stop_fn,
            post_stop=post_stop_fn,
            **options,
        )

        self.pre_start_cnt = 0
        self.post_start_cnt = 0
        self.pre_stop_cnt = 0
        self.post_stop_cnt = 0

        self.pre_start_fn_cnt = 0
        self.post_start_fn_cnt = 0
        self.pre_stop_fn_cnt = 0
        self.post_stop_fn_cnt = 0

    def pre_start(self):
        self.pre_start_cnt += 1
        super(CustomDriver, self).pre_start()

    def post_start(self):
        self.post_start_cnt += 1
        super(CustomDriver, self).post_start()

    def pre_stop(self):
        self.pre_stop_cnt += 1
        super(CustomDriver, self).pre_stop()

    def post_stop(self):
        self.post_stop_cnt += 1
        super(CustomDriver, self).post_stop()


@testsuite
class AnotherSuite:
    @testcase
    def test_driver_methods_called(self, env, result):
        assert env.custom_driver_1.status == ResourceStatus.STARTED
        assert env.custom_driver_2.status == ResourceStatus.STARTED

        assert env.custom_driver_1.pre_start_cnt == 1
        assert env.custom_driver_1.pre_start_fn_cnt == 1
        assert env.custom_driver_1.post_start_cnt == 1
        assert env.custom_driver_1.post_start_fn_cnt == 1
        assert env.custom_driver_1.pre_stop_cnt == 0
        assert env.custom_driver_1.pre_stop_fn_cnt == 0
        assert env.custom_driver_1.post_stop_cnt == 0
        assert env.custom_driver_1.post_stop_fn_cnt == 0

        assert env.custom_driver_2.pre_start_cnt == 1
        assert env.custom_driver_2.pre_start_fn_cnt == 1
        assert env.custom_driver_2.post_start_cnt == 1
        assert env.custom_driver_2.post_start_fn_cnt == 1
        assert env.custom_driver_2.pre_stop_cnt == 0
        assert env.custom_driver_2.pre_stop_fn_cnt == 0
        assert env.custom_driver_2.post_stop_cnt == 0
        assert env.custom_driver_2.post_stop_fn_cnt == 0

    @testcase
    def test_driver_restarted(self, env, result):
        env.custom_driver_1.restart()
        env.custom_driver_2.restart()
        assert env.custom_driver_1.status == ResourceStatus.STARTED
        assert env.custom_driver_2.status == ResourceStatus.STARTED

        assert env.custom_driver_1.pre_start_cnt == 2
        assert env.custom_driver_1.pre_start_fn_cnt == 2
        assert env.custom_driver_1.post_start_cnt == 2
        assert env.custom_driver_1.post_start_fn_cnt == 2
        assert env.custom_driver_1.pre_stop_cnt == 1
        assert env.custom_driver_1.pre_stop_fn_cnt == 1
        assert env.custom_driver_1.post_stop_cnt == 1
        assert env.custom_driver_1.post_stop_fn_cnt == 1

        assert env.custom_driver_2.pre_start_cnt == 2
        assert env.custom_driver_2.pre_start_fn_cnt == 2
        assert env.custom_driver_2.post_start_cnt == 2
        assert env.custom_driver_2.post_start_fn_cnt == 2
        assert env.custom_driver_2.pre_stop_cnt == 1
        assert env.custom_driver_2.pre_stop_fn_cnt == 1
        assert env.custom_driver_2.post_stop_cnt == 1
        assert env.custom_driver_2.post_stop_fn_cnt == 1


def test_multitest_driver_startup_mode(mockplan):
    """
    Make sure all methods are called once whatever a driver starts
    in async mode (default) or sequentially.
    """
    custom_driver_1 = CustomDriver(name="custom_driver_1")
    custom_driver_2 = CustomDriver(name="custom_driver_2", async_start=True)

    mockplan.add(
        MultiTest(
            name="Mtest",
            suites=[AnotherSuite()],
            environment=[custom_driver_1, custom_driver_2],
        )
    )
    mockplan.run()

    res = mockplan.result
    assert res.run is True
    assert res.report.passed is True

    assert custom_driver_1.status == ResourceStatus.STOPPED
    assert custom_driver_2.status == ResourceStatus.STOPPED

    assert custom_driver_1.pre_start_cnt == 2
    assert custom_driver_1.pre_start_fn_cnt == 2
    assert custom_driver_1.post_start_cnt == 2
    assert custom_driver_1.post_start_fn_cnt == 2
    assert custom_driver_1.pre_stop_cnt == 2
    assert custom_driver_1.pre_stop_fn_cnt == 2
    assert custom_driver_1.post_stop_cnt == 2
    assert custom_driver_1.post_stop_fn_cnt == 2

    assert custom_driver_2.pre_start_cnt == 2
    assert custom_driver_2.pre_start_fn_cnt == 2
    assert custom_driver_2.post_start_cnt == 2
    assert custom_driver_2.post_start_fn_cnt == 2
    assert custom_driver_2.pre_stop_cnt == 2
    assert custom_driver_2.pre_stop_fn_cnt == 2
    assert custom_driver_2.post_stop_cnt == 2
    assert custom_driver_2.post_stop_fn_cnt == 2
