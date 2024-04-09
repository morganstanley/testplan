#!/usr/bin/env python

from testplan.common.utils.context import context
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from testplan import test_plan
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser


NAME = "BDD style TCP example"
DESCRIPTION = "Example to show driver usage in BDD style"


@test_plan(name="BDD Example")
def main(plan):
    factory = BDDTestSuiteFactory(
        ".", default_parser=SimpleParser, feature_linked_steps=True
    )
    plan.add(
        MultiTest(
            name=NAME,
            description=DESCRIPTION,
            suites=factory.create_suites(),
            environment=[
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
    import sys

    sys.exit(not main())
