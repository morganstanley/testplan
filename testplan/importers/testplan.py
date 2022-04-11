"""
Implements one-phase importer for Testplan JSON format.
"""
import json
from typing import List

from testplan.importers import ResultImporter, ImportedResult
from testplan.report import TestGroupReport, TestReport, ReportCategories
from testplan.report.testing.schemas import TestReportSchema


class TestplanImportedResult(ImportedResult):
    """ """

    def __init__(self, result: TestReport):
        """ """
        self.result = result

    def as_test_report(self) -> TestReport:
        """ """
        return self.result

    def category(self) -> str:
        """ """
        return ReportCategories.TESTPLAN

    def results(self) -> (List[TestGroupReport]):
        """ """
        return self.result.entries


class TestplanResultImporter(ResultImporter):
    """ """

    schema = TestReportSchema()

    def __init__(self, path: str):
        """ """
        self.path = path

    def import_result(self) -> ImportedResult:
        """ """
        with open(self.path) as fp:
            result_json = json.load(fp)
            result = self.schema.load(result_json)

            return TestplanImportedResult(result)
