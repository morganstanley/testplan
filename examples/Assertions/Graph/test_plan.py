#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of assertions,
assertion groups and assertion namespaces.
"""
import os
import random
import re
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.common.utils import comparison
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SampleSuite(object):

    @testcase
    def GRAPH_TESTS(self, env, result):
        # Basic assertions contain equality, comparison, membership checks:
        result.graph('Line',
                     [
                        {'x':1, 'y':2},
                        {'x':3, 'y':4}
                     ],
                     description='Desciptions :]',
                     #options=None
                     options={'colour':'red'}
        )


@test_plan(
    name='Assertions Example',
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL,
        failing=StyleEnum.ASSERTION_DETAIL
    )
)
def main(plan):
    plan.add(MultiTest(name='Assertions Test', suites=[SampleSuite()]))


if __name__ == '__main__':
    sys.exit(not main())
