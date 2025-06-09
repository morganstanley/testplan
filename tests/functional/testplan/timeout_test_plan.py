#!/usr/bin/env python
"""Testplan that is expected to time out."""

import sys
import threading

from testplan import test_plan
from testplan.testing import multitest


@multitest.testsuite
class NormalSuite:
    @multitest.testcase
    def case(self, env, result):
        result.log("Run testcase.")


@multitest.testsuite
class TimeoutSuite:
    @multitest.testcase
    def blocks(self, env, result):
        result.log("Blocking...")
        threading.Event().wait()


@test_plan(name="Timeout example", timeout=10)
def main(plan):
    plan.add(multitest.MultiTest(name="MTest", suites=[NormalSuite()]))
    plan.add(
        multitest.MultiTest(name="Timeout MTest", suites=[TimeoutSuite()])
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
