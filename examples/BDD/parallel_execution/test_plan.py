#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser


NAME = "Parallel execution"
DESCRIPTION = "Example to show how to execute scnearios parallel"


@test_plan(name="BDD Parallel Execution Example")
def main(plan):
    factory = BDDTestSuiteFactory(
        ".", default_parser=SimpleParser, feature_linked_steps=True
    )
    plan.add(
        MultiTest(
            name=NAME, description=DESCRIPTION, suites=factory.create_suites()
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
