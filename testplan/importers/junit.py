"""
Implements three-phase importer for JUnit format.
"""
import os
from typing import List

from lxml.objectify import parse, Element

from .base import ThreePhaseFileImporter
from .suitesresults import SuitesResult
from testplan.report import (
    ReportCategories,
    TestGroupReport,
    TestCaseReport,
    RuntimeStatus,
)
from testplan.testing.multitest.entries.assertions import RawAssertion
from testplan.testing.multitest.entries.schemas.base import registry


class JUnitImportedResult(SuitesResult):
    REPORT_CATEGORY = ReportCategories.JUNIT


class JUnitResultImporter(ThreePhaseFileImporter):
    """
    Three-phase file importer class for handling JUnit format.
    """

    # For JUnit, see http://svn.apache.org/repos/asf/ant/core/trunk/src/main/org/apache/tools/ant/taskdefs/optional/junit/
    # and the JUnitResultFormatter
    def _read_data(self, path: str) -> Element:
        """
        Parses a JUnit XML report and returns root.

        :param path: path to source file
        """
        with open(path) as report_file:
            return parse(report_file).getroot()

    def _process_data(self, data: Element) -> List[TestGroupReport]:
        """
        Processes data read from the source file.

        :param data: raw data as read by the importer
        """
        result = []

        suites = data.getchildren() if data.tag == "testsuites" else [data]

        for suite in suites:
            suite_name = suite.attrib.get("name")
            # TODO: what happens if the suite_name is None or ""?
            suite_report = TestGroupReport(
                name=suite_name,
                uid=suite_name,
                category=ReportCategories.TESTSUITE,
            )

            for element in suite.getchildren():
                # Elements like properties, system-out, and system-err are
                # skipped.
                if element.tag != "testcase":
                    continue

                case_class = element.attrib.get("classname")
                case_name = element.attrib.get("name")

                if case_class is None:
                    # TODO: do we need UID to be different than name?
                    # TODO: does it need to be "{case_name} execution"?
                    case_report_uid = f"{case_name} execution"
                    if case_name == suite_report.name:
                        suite_report.name = case_name.rpartition(os.sep)[-1]
                        # TODO: does it need to be "Execution"?
                        case_report_name = "Execution"
                    else:
                        case_report_name = case_name
                else:
                    case_report_name = (
                        f"{case_class.split('.')[-1]}::{case_name}"
                    )
                    case_report_uid = (
                        f"{case_class.replace('.', '::')}::{case_name}"
                    )

                case_report = TestCaseReport(
                    name=case_report_name,
                    uid=case_report_uid,
                )

                if not element.getchildren():
                    assertion = RawAssertion(
                        description="Passed",
                        content=f"Testcase {case_name} passed",
                        passed=True,
                    )
                    case_report.append(registry.serialize(assertion))
                else:
                    for child in element.getchildren():
                        assertion = RawAssertion(
                            description=child.tag,
                            content=child.attrib.get("message"),
                            passed=child.tag not in ("failure", "error"),
                        )
                        case_report.append(registry.serialize(assertion))

                suite_report.runtime_status = RuntimeStatus.FINISHED
                suite_report.append(case_report)

            if len(suite_report):
                result.append(suite_report)

        return result

    def _create_result(
        self, raw_data: Element, processed_data: List[TestGroupReport]
    ) -> JUnitImportedResult:
        """
        Creates in-memory imported result from processed data.

        :param raw_data: raw data as read by the importer
        :param processed_data: list of data as processed by the importer
        """
        return JUnitImportedResult(
            name=self.name,
            results=processed_data,
            description=self.description,
        )
