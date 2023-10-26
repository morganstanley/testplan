"""JUnit test runner."""

import os

from lxml import etree
from schema import Or

from testplan.common.config import ConfigOption
from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    TestCaseReport,
    TestGroupReport,
)
from testplan.testing.base import ProcessRunnerTest, ProcessRunnerTestConfig
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries.base import CodeLog
from testplan.testing.multitest.entries.schemas.base import registry


class JUnitConfig(ProcessRunnerTestConfig):
    """
    Configuration object for :py:class`~testplan.testing.junit.JUnit`
    test runner.
    """

    @classmethod
    def get_options(cls):
        return {
            "results_dir": str,
            ConfigOption("junit_args", default=None): Or(list, None),
            ConfigOption("junit_filter", default=None): Or(list, None),
        }


class JUnit(ProcessRunnerTest):
    """
    Subprocess test runner for JUnit: https://junit.org/junit5/docs/current/user-guide/

    Please note that the test (either native binary or script) should generate XML format report
    so that Testplan is able to parse the result.


    .. code-block:: bash

        gradle test

    :param name: Test instance name, often used as uid of test entity.
    :type name: ``str``
    :param binary: Path to the gradle binary or script.
    :type binary: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param junit_args: Customized command line arguments for Junit test
    :type junit_args: ``NoneType`` or ``list``
    :param results_dir: Where saved the test xml report.
    :type results_dir: ``str``
    :param junit_filter: Customized command line arguments for filtering testcases.
    :type junit_filter: ``NoneType`` or ``list``

    Also inherits all
    :py:class:`~testplan.testing.base.ProcessRunnerTest` options.
    """

    CONFIG = JUnitConfig

    def __init__(
        self,
        name,
        binary,
        results_dir,
        junit_args=None,
        junit_filter=None,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(JUnit, self).__init__(**options)
        self._results_dir = None

    def _test_command(self):
        return (
            [self.resolved_bin]
            + (self.cfg.junit_args or [])
            + (self.cfg.junit_filter or [])
        )

    def _list_command(self):
        """JUnit test does not support filtering."""
        return None

    def read_test_data(self):
        """
        Read JUnit xml report.

        :return: JUnit test output.
        :rtype: ``list``
        """
        testsuites = []
        for file in sorted(os.listdir(self.cfg.results_dir)):
            _, ext = os.path.splitext(file)
            if ext == ".xml":
                try:
                    root = etree.parse(
                        os.path.join(self.cfg.results_dir, file)
                    ).getroot()
                    if root.tag == "testsuite":
                        testsuites.append(root)
                    elif root.tag == "testsuites":
                        testsuites += root.xpath("testsuite")
                    else:
                        self.logger.info(
                            "Didn't find testsuite in {}! Ignored.".format(
                                file
                            )
                        )
                except:
                    self.logger.info(
                        "{} is not a valid xml! Ignored.".format(file)
                    )
        return testsuites

    def process_test_data(self, test_data):
        """
        Convert JUnit output into a a list of report entries.

        :param test_data: JUnit test output.
        :type test_data: ``list``
        :return: list of sub reports.
        :rtype: ``list`` of (``TestGroupReport`` or ``TestCaseReport``)
        """
        result = []
        for suite in test_data:
            suite_name = suite.get("name", "JUnit testsuite")
            suite_report = TestGroupReport(
                name=suite_name,
                uid=suite_name,
                category=ReportCategories.TESTSUITE,
            )
            for case in suite.xpath("testcase"):
                case_name = case.get("name", "JUnit testcase")
                testcase_report = TestCaseReport(name=case_name, uid=case_name)
                for error in case.xpath("error"):
                    testcase_report.append(
                        registry.serialize(
                            assertions.Fail("Error executing test")
                        )
                    )
                    testcase_report.append(
                        registry.serialize(
                            CodeLog(
                                error.text,
                                language="java",
                                description="stacktrace",
                            )
                        )
                    )
                for failure in case.xpath("failure"):
                    message = failure.get("message", "testcase failure")
                    testcase_report.append(
                        registry.serialize(assertions.Fail(message))
                    )
                    if failure.text:
                        testcase_report.append(
                            registry.serialize(
                                CodeLog(
                                    failure.text,
                                    language="java",
                                    description="stacktrace",
                                )
                            )
                        )
                if not testcase_report.entries:
                    assertion_obj = assertions.RawAssertion(
                        description="Passed",
                        content="Testcase {} passed".format(case_name),
                        passed=True,
                    )
                    testcase_report.append(registry.serialize(assertion_obj))

                testcase_report.runtime_status = RuntimeStatus.FINISHED
                suite_report.append(testcase_report)
            result.append(suite_report)
        return result

    def test_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base test command with additional filtering to run a
        specific set of testcases.
        """
        cmd = self.test_command()

        if testsuite_pattern not in (
            "*",
            self._DEFAULT_SUITE_NAME,
            self._VERIFICATION_SUITE_NAME,
        ):
            raise RuntimeError(
                "Cannot run individual test suite {}".format(testsuite_pattern)
            )

        if testcase_pattern not in ("*", self._VERIFICATION_TESTCASE_NAME):
            self.logger.user_info(
                'Should run testcases in pattern "%s", but cannot run'
                " individual testcases thus will run the whole test suite",
                testcase_pattern,
            )

        return cmd + self.cfg.junit_filter if self.cfg.junit_filter else cmd

    def list_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base list command with additional filtering to list a
        specific set of testcases.
        """
        return None  # JUnit does not support listing by filter
