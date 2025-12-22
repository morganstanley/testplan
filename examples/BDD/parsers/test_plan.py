#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory

NAME = "Special Scenarios"
DESCRIPTION = "Example to show how to change parsers in step definitions"


@test_plan(name="BDD Parsers Example")
def main(plan):
    factory = BDDTestSuiteFactory(".", feature_linked_steps=True)
    plan.add(
        MultiTest(
            name=NAME, description=DESCRIPTION, suites=factory.create_suites()
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
