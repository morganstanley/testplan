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
                     [
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
                     description='Line Grap',
                     options={'colour': 'red'}
        )

        result.graph('Bar',
                     [
                         {'x': 'A', 'y': 10},
                         {'x': 'B', 'y': 5},
                         {'x': 'C', 'y': 15}
                     ],
                     description='Bar Graph',
                     options=None
        )

        result.graph('Whisker',
                     [
                         {'x': 1, 'y': 10, 'xVariance': 0.5, 'yVariance': 2},
                         {'x': 1.7, 'y': 12, 'xVariance': 1, 'yVariance': 1},
                         {'x': 2, 'y': 5, 'xVariance': 0, 'yVariance': 0},
                         {'x': 3, 'y': 15, 'xVariance': 0, 'yVariance': 2},
                         {'x': 2.5, 'y': 7, 'xVariance': 0.25, 'yVariance': 2},
                         {'x': 1.8, 'y': 7, 'xVariance': 0.25, 'yVariance': 1}
                     ],
                     description='Whisker Graph',
                     options=None
        )

        result.graph('Contour',
                     [
                         {'x': 0, 'y': 8},
                         {'x': 1, 'y': 50},
                         {'x': 2, 'y': 4},
                         {'x': -10, 'y': 9},
                         {'x': 4, 'y': 1},
                         {'x': 5, 'y': 7},
                         {'x': 6, 'y': -3},
                         {'x': 7, 'y': 3},
                         {'x': 100, 'y': 2},
                         {'x': 9, 'y': 0}
                     ],
                     description='Contour Graph',
                     options=None
         )


        result.graph('Pie',
                     [
                         {'angle': 1, 'color': '#89DAC1', 'name': 'green'},
                         {'angle': 2, 'color': '#F6D18A', 'name': 'yellow'},
                         {'angle': 5, 'color': '#1E96BE', 'name': 'cyan'},
                         {'angle': 3, 'color': '#DA70BF', 'name': 'magenta'},
                         {'angle': 5, 'color': '#F6D18A', 'name': 'yellow again'}
                     ],
                     description='Pie Chart',
                     options={
                              'colour': 'literal'
                             }
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
