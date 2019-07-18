"""
This example shows usage of graph assertions
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
        result.graph('Line',
                     {'Data Name': [
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
                     ]
                     },
                     description='Line Graph',
                     series_options={
                         'Data Name': {"colour": "red"}
                     },
                     graph_options=None
                     )

        result.graph('Bar',
                     {'Data Name': [
                         {'x': 'A', 'y': 10},
                         {'x': 'B', 'y': 5},
                         {'x': 'C', 'y': 15}
                     ]
                     },
                     description='Bar Graph',
                     series_options=None,
                     graph_options=None
                     )

        result.graph('Pie',
                     {'Data Name':  [
                                     {'angle': 1, 'color': '#89DAC1', 'name': 'green'},
                                     {'angle': 2, 'color': '#F6D18A', 'name': 'yellow'},
                                     {'angle': 5, 'color': '#1E96BE', 'name': 'cyan'},
                                     {'angle': 3, 'color': '#DA70BF', 'name': 'magenta'},
                                     {'angle': 5, 'color': '#F6D18A', 'name': 'yellow again'}
                                    ]
                      },
                     description='Pie Chart',
                     series_options={
                                            'Data Name': {'colour': 'literal'}
                                    },
                     graph_options=None
                     )
        result.graph('Line',
                     {
                         'graph 1': [
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
                         'graph 2': [
                             {'x': 1, 'y': 3},
                             {'x': 2, 'y': 5},
                             {'x': 3, 'y': 15},
                             {'x': 4, 'y': 12}
                         ]
                     },
                     description='Line Graph',
                     series_options={
                         'graph 1': {"colour": "red"},
                         'graph 2': {"colour": "blue"},
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
