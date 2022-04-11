"""
Implements three-phase importer for GoogleTest format.
"""
from typing import List

from lxml import objectify
from lxml.objectify import Element

from testplan.importers.base import T, ThreePhaseFileImporter
from testplan.importers.suitesresults import SuitesResult
from testplan.report import (
    TestGroupReport,
    ReportCategories,
    TestCaseReport,
    RuntimeStatus,
)
from testplan.testing.multitest.entries.assertions import RawAssertion
from testplan.testing.multitest.entries.schemas.base import registry


class GTestImportedResult(SuitesResult):
    REPORT_CATEGORY = ReportCategories.GTEST


class GTestResultImporter(ThreePhaseFileImporter[Element]):
    """
    Three-phase file importer class for handling GoogleTest format.
    """

    def _read_data(self, path) -> Element:
        """
        Parses a GoogleTest XML report and returns root. Assumes xUnit format.

        :param path: path to source file
        :return: root node of parsed raw test data
        """
        with open(path) as report_file:
            return objectify.parse(report_file).getroot()

    def _process_data(self, data: Element) -> List[TestGroupReport]:
        """
        Processes data read from the source file.

        :param data: raw data as read by the importer
        """
        # NOTE: XML output contains skipped testcases which are ignored.
        result = []

        for suite in data.getchildren():
            suite_name = suite.attrib["name"]
            suite_report = TestGroupReport(
                name=suite_name,
                category=ReportCategories.TESTSUITE,
            )
            suite_has_run = False

            for testcase in suite.getchildren():

                testcase_name = testcase.attrib["name"]
                testcase_report = TestCaseReport(name=testcase_name)

                if not testcase.getchildren():
                    assertion_obj = RawAssertion(
                        description="Passed",
                        content="Testcase {} passed".format(testcase_name),
                        passed=True,
                    )
                    testcase_report.append(registry.serialize(assertion_obj))
                else:
                    for entry in testcase.getchildren():
                        assertion_obj = RawAssertion(
                            description=entry.tag,
                            content=entry.text,
                            passed=entry.tag != "failure",
                        )
                        testcase_report.append(
                            registry.serialize(assertion_obj)
                        )

                testcase_report.runtime_status = RuntimeStatus.FINISHED

                if testcase.attrib["status"] != "notrun":
                    suite_report.append(testcase_report)
                    suite_has_run = True

            if suite_has_run:
                result.append(suite_report)

        return result

    def _create_result(
        self, raw_data: Element, processed_data: List[TestGroupReport]
    ) -> GTestImportedResult:
        """
        Creates in-memory imported result from processed data.

        :param raw_data: raw data as read by the importer
        :param processed_data: list of data as processed by the importer
        """
        return GTestImportedResult(
            name=self.name,
            results=processed_data,
            description=self.description,
        )
