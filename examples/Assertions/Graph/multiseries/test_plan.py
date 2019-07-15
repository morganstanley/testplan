#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of graphs
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class SampleSuite(object):

    @testcase
    def GRAPH_TESTS(self, env, result):
        # Basic assertions for graphs:
        result.graph('Line',
                     {
                                  'graph 1':[
                                                 {'x': 0, 'y': 8},
                                                 {'x': 1, 'y': 5},
                                                 {'x': 2, 'y': 4},
                                                 {'x': 3, 'y': 9},
                                                 {'x': 4, 'y': 1},
                                                 {'x': 5, 'y': 7},
                                                 {'x': 6, 'y': 6},
                                                 {'x': 7, 'y': 3},
                                                 {'x': 8, 'y': 2},
                                                 {'x': 9, 'y': 0}
                                             ],
                              'graph 2':[
                                            {'x': 1, 'y': 3},
                                            {'x': 2, 'y': 5},
                                            {'x': 3, 'y': 15},
                                            {'x': 4, 'y': 12}
                                            ]
                                  },
                     description='Line Graph',
                     individual_options={
                                    'graph 1':{"colour": "red"},
                                    'graph 2':{"colour": "blue"},
                              },
                     graph_options=None
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
