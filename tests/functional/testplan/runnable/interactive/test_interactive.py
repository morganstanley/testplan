"""Interactive mode tests."""

import os
import sys

import requests
from pytest_test_filters import skip_on_windows

from testplan import TestplanMock
from testplan.common import entity
from testplan.common.utils.comparison import compare
from testplan.common.utils.context import context
from testplan.common.utils.logger import TEST_INFO
from testplan.common.utils.timing import wait
from testplan.environment import LocalEnvironment
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.app import App
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def _assert_http_response(
    response,
    operation,
    mode,
    result=None,
    error=False,
    metadata=None,
    trace=None,
):
    assert response == {
        "result": result,
        "error": error,
        "metadata": metadata or {},
        "trace": trace,
        "message": "{} operation performed: {}".format(mode, operation),
    }


class InteractivePlan:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __enter__(self):
        self._plan = TestplanMock(**self._kwargs)
        return self._plan

    def __exit__(self, *args):
        self._plan.abort()


@testsuite
class BasicSuite:
    @testcase(parameters=range(3))
    def basic_case(self, env, result, arg):
        result.equal(1, 1, description="Passing assertion")


@testsuite(name=lambda cls_name, suite: "Custom_{}".format(suite.arg))
class TCPSuite:
    def __init__(self, arg):
        self.arg = arg

    @testcase
    def send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        bytes_sent = env.client.send_text("hello")
        received = env.server.receive_text(size=bytes_sent)
        result.equal(received, "hello", "Server received")

        bytes_sent = env.server.send_text("world")
        received = env.client.receive_text(size=bytes_sent)
        result.equal(received, "world", "Client received")


def make_multitest(idx=""):
    def accept_connection(env):
        # Server accepts client connection.
        env.server.accept_connection()

    return MultiTest(
        name="Test{}".format(idx),
        suites=[BasicSuite(), TCPSuite(0), TCPSuite(1)],
        environment=[
            TCPServer(name="server"),
            TCPClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
            ),
        ],
        after_start=accept_connection,
    )


def test_top_level_tests():
    with InteractivePlan(
        name="InteractivePlan",
        interactive_port=0,
        interactive_block=False,
        parse_cmdline=False,
        logger_level=TEST_INFO,
    ) as plan:
        plan.add(make_multitest("1"))
        plan.add(make_multitest("2"))
        plan.run()
        wait(lambda: bool(plan.i.http_handler_info), 5, raise_on_timeout=True)
        assert isinstance(plan.i.test("Test1"), MultiTest)
        assert isinstance(plan.i.test("Test2"), MultiTest)

        # print_report(plan.i.report(serialized=True))

        # TESTS AND ASSIGNED RUNNERS
        assert list(plan.i.all_tests()) == ["Test1", "Test2"]

        # OPERATE TEST DRIVERS (start/stop)
        resources = [res.uid() for res in plan.i.test("Test2").resources]
        assert resources == ["server", "client"]
        for resource in plan.i.test("Test2").resources:
            assert resource.status == resource.STATUS.NONE
        plan.i.start_test_resources("Test2")  # START
        for resource in plan.i.test("Test2").resources:
            assert resource.status == resource.STATUS.STARTED
        plan.i.stop_test_resources("Test2")  # STOP
        for resource in plan.i.test("Test2").resources:
            assert resource.status == resource.STATUS.STOPPED

        # RESET REPORTS
        plan.i.reset_all_tests()
        from .reports.basic_top_level_reset import REPORT as BTLReset

        assert (
            compare(
                BTLReset,
                plan.i.report.serialize(),
                ignore=["hash", "information", "line_no"],
            )[0]
            is True
        )

        # RUN ALL TESTS
        plan.i.run_all_tests()
        from .reports.basic_top_level import REPORT as BTLevel

        assert (
            compare(
                BTLevel,
                plan.i.report.serialize(),
                ignore=[
                    "hash",
                    "information",
                    "timer",
                    "machine_time",
                    "utc_time",
                    "file_path",
                    "line_no",
                ],
            )[0]
            is True
        )

        # RESET REPORTS
        plan.i.reset_all_tests()
        from .reports.basic_top_level_reset import REPORT as BTLReset

        assert (
            compare(
                BTLReset,
                plan.i.report.serialize(),
                ignore=["hash", "information"],
            )[0]
            is True
        )

        # RUN SINGLE TESTSUITE (CUSTOM NAME)
        plan.i.run_test_suite("Test2", "TCPSuite - Custom_1")
        from .reports.basic_run_suite_test2 import REPORT as BRSTest2

        assert (
            compare(BRSTest2, plan.i.test_report("Test2"), ignore=["hash"])[0]
            is True
        )

        # RUN SINGLE TESTCASE
        plan.i.run_test_case("Test1", "*", "basic_case__arg_1")
        from .reports.basic_run_case_test1 import REPORT as BRCTest1

        assert (
            compare(
                BRCTest1,
                plan.i.test_report("Test1"),
                ignore=[
                    "hash",
                    "information",
                    "timer",
                    "machine_time",
                    "utc_time",
                    "file_path",
                    "line_no",
                ],
            )[0]
            is True
        )


def test_top_level_environment():
    with InteractivePlan(
        name="InteractivePlan",
        interactive_port=0,
        interactive_block=False,
        parse_cmdline=False,
        logger_level=TEST_INFO,
    ) as plan:
        plan.add_environment(
            LocalEnvironment(
                "env1",
                [
                    TCPServer(name="server"),
                    TCPClient(
                        name="client",
                        host=context("server", "{{host}}"),
                        port=context("server", "{{port}}"),
                    ),
                ],
            )
        )
        plan.run()
        wait(lambda: bool(plan.i.http_handler_info), 5, raise_on_timeout=True)

        assert len(plan.resources.environments.envs) == 1

        # Create an environment using serializable arguments.
        # That is mandatory for HTTP usage.
        plan.i.create_new_environment("env2")
        plan.i.add_environment_resource("env2", "TCPServer", name="server")
        plan.i.add_environment_resource(
            "env2",
            "TCPClient",
            name="client",
            _ctx_host_ctx_driver="server",
            _ctx_host_ctx_value="{{host}}",
            _ctx_port_ctx_driver="server",
            _ctx_port_ctx_value="{{port}}",
        )
        plan.i.add_created_environment("env2")

        assert len(plan.resources.environments.envs) == 2

        for env_uid in ("env1", "env2"):
            env = plan.i.get_environment(env_uid)
            assert isinstance(env, entity.Environment)
            resources = [res.uid() for res in env]
            assert resources == ["server", "client"]
            for resource in env:
                assert resource.status == resource.STATUS.NONE
            plan.i.start_environment(env_uid)  # START

            # INSPECT THE CONTEXT WHEN STARTED
            env_context = plan.i.get_environment_context(env_uid)
            for resource in [res.uid() for res in env]:
                res_context = plan.i.environment_resource_context(
                    env_uid, resource_uid=resource
                )
                assert env_context[resource] == res_context
                assert isinstance(res_context["host"], str)
                assert isinstance(res_context["port"], int)
                assert res_context["port"] > 0

            # CUSTOM RESOURCE OPERATIONS
            plan.i.environment_resource_operation(
                env_uid, "server", "accept_connection"
            )
            plan.i.environment_resource_operation(
                env_uid, "client", "send_text", msg="hello"
            )
            received = plan.i.environment_resource_operation(
                env_uid, "server", "receive_text"
            )
            assert received == "hello"
            plan.i.environment_resource_operation(
                env_uid, "server", "send_text", msg="worlds"
            )
            received = plan.i.environment_resource_operation(
                env_uid, "client", "receive_text"
            )
            assert received == "worlds"

            for resource in env:
                assert resource.status == resource.STATUS.STARTED
            plan.i.stop_environment(env_uid)  # STOP
            for resource in env:
                assert resource.status == resource.STATUS.STOPPED


def put_request(url, data):
    headers = {"content-type": "application/json"}
    return requests.put(url, headers=headers, json=data)


@skip_on_windows(reason="Failing on windows, disable for now")
def test_env_operate():
    with InteractivePlan(
        name="InteractivePlan",
        interactive_port=0,
        interactive_block=False,
        parse_cmdline=False,
        logger_level=TEST_INFO,
    ) as plan:

        plan.add(make_multitest("1"))
        plan.add(make_multitest("2"))

        plan.run()
        wait(
            lambda: plan.i.http_handler_info[0] is not None,
            5,
            raise_on_timeout=True,
        )
        addr = "http://{}:{}".format(*plan.i.http_handler_info)

        response = requests.get(f"{addr}/api/v1/interactive/report/tests")
        assert response.ok

        current_report = response.json()
        assert len(current_report) == 2

        for resource in plan.i.test("Test2").resources:
            assert resource.status == resource.STATUS.NONE

        test2_report = current_report[1].copy()
        assert test2_report["name"] == "Test2"

        # Start env
        test2_report["env_status"] = entity.ResourceStatus.STARTING
        response = put_request(
            url=f"{addr}/api/v1/interactive/report/tests/Test2",
            data=test2_report,
        )
        assert response.ok

        current_test2_report = plan.i.report["Test2"]
        assert current_test2_report.env_status in (
            entity.ResourceStatus.STARTING,
            entity.ResourceStatus.STARTED,
        )

        wait(
            lambda: plan.i.report["Test2"].env_status
            == entity.ResourceStatus.STARTED,
            5,
            raise_on_timeout=True,
        )

        response = requests.get(
            f"{addr}/api/v1/interactive/report/tests/Test2"
        )
        assert response.ok
        test2_report = response.json()
        assert test2_report["env_status"] == entity.ResourceStatus.STARTED

        # Stop env
        test2_report["env_status"] = entity.ResourceStatus.STOPPING
        response = put_request(
            url=f"{addr}/api/v1/interactive/report/tests/Test2",
            data=test2_report,
        )
        assert response.ok

        current_test2_report = plan.i.report["Test2"]
        assert current_test2_report.env_status in (
            entity.ResourceStatus.STOPPING,
            entity.ResourceStatus.STOPPED,
        )
        wait(
            lambda: plan.i.report["Test2"].env_status
            == entity.ResourceStatus.STOPPED,
            5,
            raise_on_timeout=True,
        )

        response = requests.get(
            f"{addr}/api/v1/interactive/report/tests/Test2"
        )
        assert response.ok
        test2_report = response.json()
        assert test2_report["env_status"] == entity.ResourceStatus.STOPPED


def test_abort_plan():
    with InteractivePlan(
        name="InteractivePlan",
        interactive_port=0,
        interactive_block=False,
        parse_cmdline=False,
        logger_level=TEST_INFO,
    ) as plan:
        multitest = MultiTest(
            name="MultiTest",
            suites=[BasicSuite()],
            environment=[
                App(
                    name="app",
                    binary=sys.executable,
                    args=["-c", "import sys; sys.exit(0)"],
                )
            ],
        )
        plan.add(multitest)
        plan.run()

        plan.i.start_test_resources("MultiTest")
        for resource in plan.i.test("MultiTest").resources:
            wait(
                lambda: resource.status == resource.STATUS.STARTED,
                5,
                raise_on_timeout=True,
            )
        plan.abort()
        for resource in plan.i.test("MultiTest").resources:
            wait(
                lambda: resource.status == resource.STATUS.STOPPED,
                5,
                raise_on_timeout=True,
            )
