"""PyUnit test runner."""

from testplan.testing import base as testing
from testplan.report import testing as report_testing
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries import schemas
from testplan.testing.multitest.entries import base as base_entries

import unittest


class PyUnitConfig(testing.TestConfig):
    """
    Configuration object for :py:class`~testplan.testing.pyunit.PyUnit` test
    runner.
    """

    @classmethod
    def get_options(cls):
        return {"suite": unittest.suite.TestSuite}


class PyUnit(testing.Test):
    """
    Test runner for PyUnit unit tests.

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param suite: PyUnit testsuite
    :type suite: :py:class:`~unittest.suite.TestSuite`
    :param description: Description of test instance.
    :type description: ``str``

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = PyUnitConfig
    _TESTCASE_NAME = "PyUnit test results"

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results)

    def run_tests(self):
        """Run PyUnit and wait for it to terminate."""
        suite_result = unittest.TestResult()
        self.cfg.suite.run(suite_result)

        # Since we can't reliably inspect the individual testcases of a PyUnit
        # suite, we put all results into a single "testcase" report. This
        # will only list failures and errors and not give detail on individual
        # assertions like with MultiTest.
        testcase_report = report_testing.TestCaseReport(
            name=self._TESTCASE_NAME
        )

        for call, error in suite_result.errors:
            assertion_obj = assertions.RawAssertion(
                description=str(call), content=str(error).strip(), passed=False
            )
            testcase_report.append(
                schemas.base.registry.serialize(assertion_obj)
            )

        for call, error in suite_result.failures:
            assertion_obj = assertions.RawAssertion(
                description=str(call), content=str(error).strip(), passed=False
            )
            testcase_report.append(
                schemas.base.registry.serialize(assertion_obj)
            )

        # In case of no failures or errors we need to explicitly mark the
        # testsuite as passed.
        if not testcase_report.entries:
            log_entry = base_entries.Log(
                "All PyUnit testcases passed", description="PyUnit success"
            )
            testcase_report.append(schemas.base.registry.serialize(log_entry))

        self.result.report.append(testcase_report)

    def get_test_context(self):
        """
        Currently we do not inspect individual PyUnit testcases - only allow
        the whole suite to be run.
        """
        return [self._TESTCASE_NAME, []]

    def dry_run(self):
        """Return an empty report tree."""
        report = self._new_test_report()
        testcase_report = report_testing.TestCaseReport(
            name=self._TESTCASE_NAME
        )
        report.append(testcase_report)

        return report
