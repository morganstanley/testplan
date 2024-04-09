#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser
from testplan.testing.bdd.bdd_tools import ContextResolver


NAME = "Context Resolution"
DESCRIPTION = "Example to show how to refer context values from gherkin "


@test_plan(name="BDD Example")
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
