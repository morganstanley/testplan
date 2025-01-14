"""
Implements one-phase importer for Testplan JSON format.
"""
import os
import pathlib
from typing import List

from testplan.common.utils.json import json_loads
from testplan.defaults import ATTACHMENTS
from testplan.importers import ImportedResult, ResultImporter
from testplan.report import ReportCategories, TestGroupReport, TestReport
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
            result_json = json_loads(fp.read())
            self.fix_attachments_path(result_json)
            result = self.schema.load(result_json)

            return TestplanImportedResult(result)

    def fix_attachments_path(
        self,
        report: dict,
        attachment_dir: pathlib.Path = None,
    ):
        """
        Best effort fix attachment path in case report.json and _attachments are copied around
        """
        attachment_dir = (
            str(attachment_dir)
            if attachment_dir
            else os.path.join(os.path.dirname(self.path), ATTACHMENTS)
        )
        if report.get("attachments"):
            for dst, src in report["attachments"].items():
                if os.path.isfile(src):
                    # attachment path is correct
                    break
                else:
                    # attempt to fix attachment path
                    alt_src = os.path.join(attachment_dir, dst)
                    if os.path.isfile(alt_src):
                        report["attachments"][dst] = alt_src

        # recursively fix entries
        def _fix_attachments_path(report):
            if report.get("entries"):
                for entry in report["entries"]:
                    _fix_attachments_path(entry)
            elif report.get("source_path") and report.get("dst_path"):
                if os.path.isfile(report["source_path"]):
                    # attachment path is correct
                    return
                alt_src = os.path.join(attachment_dir, report["dst_path"])
                if os.path.isfile(alt_src):
                    report["source_path"] = alt_src

        _fix_attachments_path(report)
        return report
