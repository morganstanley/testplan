"""
Base class for exporters that upload assertions per task.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Set

from testplan.common.exporters import ExportContext, verify_export_context
from testplan.report.testing.base import (
    TestCaseReport,
    TestGroupReport,
    TestReport,
)
from testplan.report.testing.schemas import TestReportSchema

from .base import Exporter
from .json import JSONExporter


def collect_assertions(
    report: TestGroupReport, assertions: Dict[str, List[Any]]
) -> None:
    """Map testcase uid to its assertion entries."""
    for entry in report:
        if isinstance(entry, TestCaseReport):
            assertions[entry.uid] = entry.entries
        elif isinstance(entry, TestGroupReport):
            collect_assertions(entry, assertions)


class TaskExporter(Exporter):
    """
    Uploads assertions of each task in a background thread as soon as
    the task finishes, then uploads the report structure at the end.

    Subclasses implement :py:meth:`upload_assertions` and
    :py:meth:`upload_structure`.
    """

    # Subclasses may use an extended schema
    schema = TestReportSchema

    def __init__(self, name: Optional[str] = None, **options: Any) -> None:
        super().__init__(name=name, **options)
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=self.__class__.__name__
        )
        self._uploaded: Set[str] = set()

    def upload_assertions(
        self, test_uid: str, assertions: Dict[str, List[Any]]
    ) -> None:
        """
        Upload assertions of one top-level test.

        :param test_uid: uid of the top-level test report
        :param assertions: testcase uid to its assertion entries
        """
        raise NotImplementedError(
            "TaskExporter must define upload_assertions()."
        )

    def upload_structure(
        self, meta: Dict[str, Any], structure: List[Dict[str, Any]]
    ) -> Optional[Dict]:
        """
        Upload the base report and its structure, called once at the end.

        :param meta: serialized report without entries
        :param structure: serialized top-level tests without assertions
        :return: dictionary containing the possible output
        """
        raise NotImplementedError(
            "TaskExporter must define upload_structure()."
        )

    def submit_task(self, report: TestGroupReport) -> None:
        """
        Queue assertions of a finished task for upload. Called from the
        executor thread which stored the task result.
        """
        report_filter = getattr(self.cfg, "reporting_exclude_filter", None)
        if report_filter is not None:
            report = report_filter(report)
            # Nothing left to upload
            if not len(report):
                return

        assertions: Dict[str, List[Any]] = {}
        # a json dump is expensive so we work on the report object directly
        collect_assertions(report, assertions)
        try:
            self._executor.submit(self._upload, report.uid, assertions)
        except RuntimeError:
            self.logger.warning(
                "Upload of %s not queued, %s stopped", report.uid, self
            )

    def _upload(self, test_uid: str, assertions: Dict[str, List[Any]]) -> None:
        try:
            self.upload_assertions(test_uid, assertions)
        except Exception as exc:
            self.logger.error(
                "Failed to upload assertions of %s: %s", test_uid, exc
            )
        else:
            self._uploaded.add(test_uid)

    def drain(self) -> None:
        """Wait for all queued uploads to finish."""
        self._executor.shutdown(wait=True)

    def stop(self) -> None:
        """Cancel queued uploads without waiting."""
        self._executor.shutdown(wait=False, cancel_futures=True)

    def export(
        self,
        source: TestReport,
        export_context: ExportContext,
    ) -> Optional[Dict]:
        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        # Report entries must not change before this
        self.drain()

        data = self.schema().dump(source)
        meta, structure, assertions_map = JSONExporter.split_json_report(data)
        for test in structure:
            if test["uid"] in self._uploaded:
                continue
            # Leftover or failed upload, send again
            self.upload_assertions(
                test["uid"], assertions_map[f"assertions_{test['uid']}"]
            )
        return self.upload_structure(meta, structure)
