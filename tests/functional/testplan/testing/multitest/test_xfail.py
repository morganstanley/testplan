
from testplan.testing.multitest import MultiTest, testsuite, testcase, xfail

from testplan import Testplan
from testplan.runners.pools import ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.report.testing import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class StrictXfailedSuite(object):
    """A test suite with parameterized testcases."""

    @testcase(
        parameters=tuple(range(10))
    )
    @xfail('Should be fail', strict=True)
    def test_fail(self, env, result, val):
        result.true(val > 100, description='Check if value is true')

    @testcase(
        parameters=tuple(range(10))
    )
    @xfail('Should be pass', strict=True)
    def test_pass(self, env, result, val):
        result.true(val < 100, description='Check if value is true')


@testsuite
class NoStrictXfailedSuite(object):
    """A test suite with parameterized testcases."""

    @testcase(
        parameters=tuple(range(10))
    )
    @xfail('Should be fail', strict=False)
    def test_fail(self, env, result, val):
        result.true(val > 100, description='Check if value is true')

    @testcase(
        parameters=tuple(range(10))
    )
    @xfail('Should be pass', strict=False)
    def test_pass(self, env, result, val):
        result.true(val < 100, description='Check if value is true')


def test_xfail():
    plan = Testplan(name='plan', parse_cmdline=False)
    plan.add(
        MultiTest(
            name='xfail_test',
            suites=[StrictXfailedSuite(), NoStrictXfailedSuite()]
        )
    )
    result = plan.run()

    assert result.report.passed is False

    strict_xfail_suite_report = result.report.entries[0].entries[0]
    assert strict_xfail_suite_report.passed is False
    assert strict_xfail_suite_report.entries[0].passed is True
    assert strict_xfail_suite_report.entries[1].passed is False

    no_strict_xfail_suite_report = result.report.entries[0].entries[1]
    assert no_strict_xfail_suite_report.entries[0].passed is True
    assert no_strict_xfail_suite_report.entries[1].passed is True
