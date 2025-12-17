#!/usr/bin/env python
import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.exporters.testing import WebServerExporter


@testsuite
class Alpha:
    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")


@test_plan(name="Multiply Programmatic", exporters=WebServerExporter())
def main(plan):
    test = MultiTest(name="MultiplyTest", suites=[Alpha()])
    plan.add(test)


if __name__ == "__main__":
    sys.exit(not main())
