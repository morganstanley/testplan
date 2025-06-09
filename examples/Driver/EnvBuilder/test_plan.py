#!/usr/bin/env python
"""
This example demonstrates usage of callable object to construct environment,
intial_context and dependencies for a multitest at runtime.
"""

import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from env_builder import EnvBuilder
from suites import TestOneClient, TestTwoClients


@test_plan(name="EnvBuilderExample")
def main(plan):
    env_builder1 = EnvBuilder("One Client", ["client1", "server1"])
    env_builder2 = EnvBuilder("Two Clients", ["client1", "client2", "server1"])
    plan.add(
        MultiTest(
            name="TestOneClient",
            suites=[TestOneClient()],
            environment=env_builder1.build_env,
            dependencies=env_builder1.build_deps,
            initial_context=env_builder1.init_ctx,
        )
    )

    plan.add(
        MultiTest(
            name="TestTwoClients",
            suites=[TestTwoClients()],
            environment=env_builder2.build_env,
            dependencies=env_builder2.build_deps,
            initial_context=env_builder2.init_ctx,
        )
    )


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
