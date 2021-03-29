from testplan.common.utils.testing import (
    log_propagation_disabled,
)
from testplan import TestplanMock
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class AlphaSuite(object):
    @testcase
    def test_pass(self, env, result):
        result.true(True)


def test_label():
    mockplan = TestplanMock(name="test_label", label="my_label")

    multitest = MultiTest(
        name="MyMultitest",
        suites=[AlphaSuite()],
    )
    mockplan.add(multitest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        mockplan.run()

    assert mockplan.report.label == "my_label"
