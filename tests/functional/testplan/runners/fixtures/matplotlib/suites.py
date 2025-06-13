"""Test Multitest - Test Suite - Result - Test Report - Exporter integration"""

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plot

from testplan.testing.multitest import MultiTest, testsuite, testcase


@testsuite
class MySuite:
    @testcase
    def test_matplot(self, env, result):
        x = range(0, 10)
        y = range(0, 10)
        plot.plot(x, y)

        result.matplot(plot, width=2, height=2, description="My matplot")


def make_multitest():
    return MultiTest(name="MyMultitest", suites=[MySuite()])
