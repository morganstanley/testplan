#!/usr/bin/env python
"""Testplan that is expected to time out."""
import sys
import threading

import testplan
from testplan.testing import multitest


@multitest.testsuite
class TimeoutSuite(object):

    @multitest.testcase
    def blocks(self, env, result):
        result.log('Blocking...')
        threading.Event().wait()


@testplan.test_plan(name='Timeout example',
                    timeout=5)
def main(plan):
    plan.add(multitest.MultiTest(name='Timeout MTest',
                                 suites=[TimeoutSuite()]))


if __name__ == '__main__':
    sys.exit(main().exit_code)

