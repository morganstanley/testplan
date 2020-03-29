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
        return {"testcases": [type(unittest.TestCase)]}


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

    def __init__(self, name, testcases, **kwargs):
        super(PyUnit, self).__init__(name=name, testcases=testcases, **kwargs)
        self._pyunit_testcases = {
            testcase.__name__: testcase for testcase in self.cfg.testcases
        }

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results)

    def run_tests(self):
        """Run PyUnit and wait for it to terminate."""
        self.result.report.extend(self._run_tests())

    def get_test_context(self):
        """
        Currently we do not inspect individual PyUnit testcases - only allow
        the whole suite to be run.
        """
        return [self._TESTSUITE_NAME, [self._TESTCASE_NAME]]

    def dry_run(self):
        """Return an empty report tree."""
        test_report = self._new_test_report()

        for pyunit_testcase in self.cfg.testcases:
            testsuite_report = report_testing.TestGroupReport(
                name=pyunit_testcase.__name__,
                uid=pyunit_testcase.__name__,
                category=report_testing.ReportCategories.TESTSUITE,
                entries=[
                    report_testing.TestCaseReport(
                        name=self._TESTCASE_NAME, uid=self._TESTCASE_NAME,
                    )
                ],
            )
            test_report.append(testsuite_report)

        result = testing.TestResult()
        result.report = test_report

        return result

    def run_testcases_iter(self, testsuite_pattern="*", testcase_pattern="*"):
        """Run testcases and yield testcase report and parent UIDs."""
        if testsuite_pattern == "*":
            for testsuite_report in self._run_tests():
                yield testsuite_report[self._TESTCASE_NAME], [
                    self.cfg.name,
                    testsuite_report.uid,
                ]
        else:
            testsuite_report = self._run_testsuite(
                self._pyunit_testcases[testsuite_pattern]
            )
            yield testsuite_report[self._TESTCASE_NAME], [
                self.cfg.name,
                testsuite_report.uid,
            ]

    def _run_tests(self):
        """Run tests and yield testsuite reports."""
        for pyunit_testcase in self.cfg.testcases:
            yield self._run_testsuite(pyunit_testcase)

    def _run_testsuite(self, pyunit_testcase):
        """Run a single PyUnit Testcase as a suite and return a testsuite report."""
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            pyunit_testcase
        )
        suite_result = unittest.TextTestRunner().run(suite)

        # Since we can't reliably inspect the individual testcases of a PyUnit
        # suite, we put all results into a single "testcase" report. This
        # will only list failures and errors and not give detail on individual
        # assertions like with MultiTest.
        testcase_report = report_testing.TestCaseReport(
            name=self._TESTCASE_NAME, uid=self._TESTCASE_NAME
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

        # We have to wrap the testcase report in a testsuite report.
        return report_testing.TestGroupReport(
            name=pyunit_testcase.__name__,
            uid=pyunit_testcase.__name__,
            category=report_testing.ReportCategories.TESTSUITE,
            entries=[testcase_report],
        )
