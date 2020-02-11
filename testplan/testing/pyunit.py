"""PyUnit test runner."""

from testplan.testing import base as testing
from testplan.report import testing as report_testing
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries import schemas

import unittest


class PyUnitConfig(testing.TestConfig):
    """
    Configuration object for :py:class`~testplan.testing.pyunit.PyUnit` test
    runner.
    """

    @classmethod
    def get_options(cls):
        return {"suites": [unittest.suite.TestSuite]}


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

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results)

    def run_tests(self):
        """Run PyUnit and wait for it to terminate."""
        for pyunit_suite in self.cfg.suites:
            suite_report = self._run_pyunit_suite(pyunit_suite)
            self.result.report.append(suite_report)

    def _run_pyunit_suite(self, pyunit_suite):
        """
        Run a single PyUnit testsuite and return the results as a suite report.
        """
        suite_result = unittest.TestResult()
        pyunit_suite.run(suite_result)

        # Since we can't reliably inspect the individual testcases of a PyUnit
        # suite, we put all results into a single "testcase" report. This
        # will only list failures and errors and not give detail on individual
        # assertions like with MultiTest.
        testcase_report = report_testing.TestCaseReport(name="PyUnit results")

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
        testcase_report.pass_if_empty()

        # Store the testcase reoport inside a testsuite report, and return it.
        suite_report = report_testing.TestGroupReport(
            name=self.cfg.name, category="testsuite"
        )
        suite_report.append(testcase_report)
        return suite_report

    def get_test_context(self):
        """TODO find out if we can inspect suites/testcases."""
        return []
