#!/usr/bin/env python

from testplan import test_plan
from testplan.testing.multitest import MultiTest
from testplan.testing.bdd import BDDTestSuiteFactory
from testplan.testing.bdd.parsers import SimpleParser


@test_plan(name="BDD Common Steps Example")
def main(plan):
    factory1 = BDDTestSuiteFactory(
        "features/feature1",
        default_parser=SimpleParser,
        common_step_dirs=["features/steps"],
    )
    factory2 = BDDTestSuiteFactory(
        "features/feature2",
        default_parser=SimpleParser,
        common_step_dirs=["features/steps"],
    )
    plan.add(
        MultiTest(
            name="Example Gherkin Test",
            description="Example Gherkin Suites",
            suites=[*factory1.create_suites(), *factory2.create_suites()],
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
