#!/usr/bin/env python

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum
from testplan.environment import LocalEnvironment
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient
from testplan.common.utils.context import context

from my_tests.mtest import make_multitest

# Hard coding interactive mode usage.
@test_plan(
    name="MyPlan",
    interactive=True,
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    # Add a test with an environment.
    plan.add(make_multitest(idx="1"))

    # Add an independent environment.
    plan.add_environment(
        LocalEnvironment(
            "my_env1",
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


if __name__ == "__main__":
    sys.exit(not main())


# INTERACTIVE MODE DEMO:
# ----------------------
#
# When HTTP handler starts listening on <IP>:$PORT
# use a tool like curl to send HTTP requests and operate the environments.
#
# Operate test environment:
#     Start the test env:
#         curl -X POST http://127.0.0.1:$PORT/sync/start_test_resources -d '{"test_uid": "Test1"}'
#     Send a message from client:
#         curl -X POST http://127.0.0.1:$PORT/sync/test_resource_operation -d '{"test_uid": "Test1", "resource_uid": "client", "operation": "send_text", "msg": "Hello"}'
#     Receive it from server:
#         curl -X POST http://127.0.0.1:$PORT/sync/test_resource_operation -d '{"test_uid": "Test1", "resource_uid": "server", "operation": "receive_text"}'
#     Stop the test env:
#         curl -X POST http://127.0.0.1:$PORT/sync/stop_test_resources -d '{"test_uid": "Test1"}'
#
# Add dynamically an environment:
#     Create an environment container:
#         curl -X POST http://127.0.0.1:$PORT/sync/create_new_environment -d '{"env_uid": "env1"}'
#     Add a server:
#         curl -X POST http://127.0.0.1:$PORT/sync/add_environment_resource -d '{"env_uid": "env1", "target_class_name": "TCPServer", "name": "server"}'
#     Add a client using the context convention mechanism:
#         curl -X POST http://127.0.0.1:$PORT/sync/add_environment_resource -d '{"env_uid": "env1", "target_class_name": "TCPClient", "name": "client", "_ctx_host_ctx_driver": "server", "_ctx_host_ctx_value": "{{host}}","_ctx_port_ctx_driver": "server", "_ctx_port_ctx_value": "{{port}}"}'
#     Add the created environment to the plan:
#         curl -X POST http://127.0.0.1:$PORT/sync/add_created_environment -d '{"env_uid": "env1"}'
#
#     Operate the new added environment env1:
#         curl -X POST http://127.0.0.1:$PORT/sync/start_environment -d '{"env_uid": "env1"}'
#         curl -X POST http://127.0.0.1:$PORT/sync/environment_resource_operation -d '{"env_uid": "env1", "resource_uid": "server", "operation": "accept_connection"}'
#         curl -X POST http://127.0.0.1:$PORT/sync/environment_resource_operation -d '{"env_uid": "env1", "resource_uid": "client", "operation": "send_text", "msg": "Hello"}'
#         curl -X POST http://127.0.0.1:$PORT/sync/environment_resource_operation -d '{"env_uid": "env1", "resource_uid": "server", "operation": "receive_text"}'
#         curl -X POST http://127.0.0.1:$PORT/sync/stop_environment -d '{"env_uid": "env1"}'
#
