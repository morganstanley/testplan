"""PyUnit test runner."""

import unittest
from typing import Generator, Dict

from testplan.testing import base as testing
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries import schemas
from testplan.testing.multitest.entries import base as entries_base
from testplan.report import (
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    RuntimeStatus,
)


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

    :param name: Test instance name, often used as uid of test entity.
    :type name: ``str``
    :param testcases: PyUnit testcases.
    :type testcases: :py:class:`~unittest.TestCase`
    :param description: Description of test instance.
    :type description: ``str``

    Also inherits all :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = PyUnitConfig
    _TESTCASE_NAME = "PyUnit test results"

    def __init__(self, name, testcases, description=None, **kwargs):
        super(PyUnit, self).__init__(
            name=name, testcases=testcases, description=description, **kwargs
        )
        self._pyunit_testcases = {
            testcase.__name__: testcase for testcase in self.cfg.testcases
        }

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results)

    def run_tests(self):
        """Run PyUnit and wait for it to terminate."""
        with self.report.timer.record("run"):
            self.result.report.extend(self._run_tests())

    def get_test_context(self):
        """
        Currently we do not inspect individual PyUnit testcases - only allow
        the whole suite to be run.
        """
        return [
            (testcase, [testcase])
            for testcase in self._pyunit_testcases.keys()
        ]

    def dry_run(self):
        """Return an empty report tree."""
        self.result.report = self._new_test_report()

        for pyunit_testcase in self.cfg.testcases:
            testsuite_report = TestGroupReport(
                name=pyunit_testcase.__name__,
                uid=pyunit_testcase.__name__,
                category=ReportCategories.TESTSUITE,
                entries=[
                    TestCaseReport(
                        name=self._TESTCASE_NAME, uid=self._TESTCASE_NAME
                    )
                ],
            )
            self.result.report.append(testsuite_report)

        return self.result

    def run_testcases_iter(
        self,
        testsuite_pattern: str = "*",
        testcase_pattern: str = "*",
        shallow_report: Dict = None,
    ) -> Generator:
        """
        Run all testcases and yield testcase reports.

        :param testsuite_pattern: pattern to match for testsuite names
        :param testcase_pattern: pattern to match for testcase names
        :param shallow_report: shallow report entry
        :return: generator yielding testcase reports and UIDs for merge step
        """
        if testsuite_pattern == "*":
            yield {"runtime_status": RuntimeStatus.RUNNING}, [self.uid()]
            for testsuite_report in self._run_tests():
                yield testsuite_report[self._TESTCASE_NAME], [
                    self.uid(),
                    testsuite_report.uid,
                ]
        else:
            yield {"runtime_status": RuntimeStatus.RUNNING}, [
                self.uid(),
                testsuite_pattern,
            ]
            testsuite_report = self._run_testsuite(
                self._pyunit_testcases[testsuite_pattern]
            )
            yield testsuite_report[self._TESTCASE_NAME], [
                self.uid(),
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
        testcase_report = TestCaseReport(
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
            log_entry = entries_base.Log(
                "All PyUnit testcases passed", description="PyUnit success"
            )
            testcase_report.append(schemas.base.registry.serialize(log_entry))

        testcase_report.runtime_status = RuntimeStatus.FINISHED

        # We have to wrap the testcase report in a testsuite report.
        return TestGroupReport(
            name=pyunit_testcase.__name__,
            uid=pyunit_testcase.__name__,
            category=ReportCategories.TESTSUITE,
            entries=[testcase_report],
        )
