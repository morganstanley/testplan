#!/usr/bin/env python
"""
Demostrates Zookeeper driver usage from within the testcases.
"""

import os
import sys

try:
    from kazoo.client import KazooClient
except ImportError:
    print("Cannot import kazoo!")
    exit()

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.driver.zookeeper import (
    ZookeeperStandalone,
    ZK_SERVER,
)
from testplan.testing.multitest import testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


@testsuite
class ZookeeperTest(object):
    """Suite that contains testcases that perform zookeeper operation."""

    def setup(self, env, result):
        """
        Setup method that will be executed before all testcases. It is
        used to ensure the path that the testcases require.
        """
        zk = KazooClient(hosts="127.0.0.1:{}".format(env.zk.port))
        zk.start()
        zk.ensure_path("/testplan")

    @testcase
    def get_node(self, env, result):
        """Get and log node information example."""
        zk = KazooClient(hosts="127.0.0.1:{}".format(env.zk.port))
        zk.start()
        node = zk.get("/")
        result.log(node)

    @testcase
    def create_node(self, env, result):
        """Create node example."""
        zk = KazooClient(hosts="127.0.0.1:{}".format(env.zk.port))
        zk.start()
        test_value = b"testplan"
        zk.create("/testplan/test", test_value)
        data, _ = zk.get("/testplan/test")
        result.equal(data, test_value)


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="ZookeeperExample",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    pdf_path="report.pdf",
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    cfg_template = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "zoo_template.cfg"
    )

    plan.add(
        MultiTest(
            name="ZookeeperTest",
            suites=[ZookeeperTest()],
            environment=[
                ZookeeperStandalone(name="zk", cfg_template=cfg_template)
            ],
        )
    )


if __name__ == "__main__":
    if os.path.exists(ZK_SERVER):
        sys.exit(not main())
    else:
        print("Zookeeper doesn't exist in this server.")
