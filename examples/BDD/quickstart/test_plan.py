#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser


@test_plan(name="Example Gherkin Testplan")
def main(plan):
    factory = BDDTestSuiteFactory("features", default_parser=SimpleParser)
    plan.add(
        MultiTest(
            name="Example Gherkin Test",
            description="Example Gherkin Suite",
            suites=factory.create_suites(),
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
