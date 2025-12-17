#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser
from testplan.testing.bdd.bdd_tools import ContextResolver


NAME = "Special Scenarios"
DESCRIPTION = "Example to show how how to hook up setup/teardown pre_testcase/post_testcase"


@test_plan(name="BDD Special Scenarios Example")
def main(plan):
    factory = BDDTestSuiteFactory(
        ".",
        default_parser=SimpleParser,
        feature_linked_steps=True,
        resolver=ContextResolver(),
    )
    plan.add(
        MultiTest(
            name=NAME, description=DESCRIPTION, suites=factory.create_suites()
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
