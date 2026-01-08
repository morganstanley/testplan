import pathlib
from enum import IntEnum
from typing import Optional, Dict
from testplan.report import TestReport, ReportCategories, TestGroupReport
from testplan.common.config import ConfigOption
from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    verify_export_context,
)
from testplan.exporters.testing.base import Exporter


class FailedTestLevel(IntEnum):
    """
    Enum representing the different levels of failed tests that can be exported.
    """

    MULTITEST = 1
    TESTSUITE = 2
    TESTCASE = 3

    def __str__(self):
        return self.name.lower()


class FailtedTestsExporterConfig(ExporterConfig):
    """
    Configuration object for :py:class:`~FailedTestsExporter`.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("dump_failed_tests"): str,
            ConfigOption("failed_tests_level"): FailedTestLevel,
        }


class FailedTestsExporter(Exporter):
    """
    Exporter for failed tests.

    This exporter is used to generate reports for tests that have failed.
    """

    CONFIG = FailtedTestsExporterConfig

    def __init__(self, name="Failed tests exporter", **options):
        super().__init__(name=name, **options)

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> None:
        """
        Export failed tests from the given test report.

        :param source: The test report to export from.
        :param export_context: Context for the export operation.
        :return: A dictionary containing the exported data.
        """
        verify_export_context(exporter=self, export_context=export_context)
        failed_test_path = pathlib.Path(self.cfg.dump_failed_tests).resolve()
        if source.is_empty():
            return

        failed_tests = set()

        for test_grp_report in source:
            if not test_grp_report.failed:
                continue

            if test_grp_report.category == ReportCategories.SYNTHESIZED:
                continue

            if (
                self.cfg.failed_tests_level == FailedTestLevel.MULTITEST
                or test_grp_report.category == ReportCategories.ERROR
            ):
                failed_tests.add(test_grp_report.name)
                continue

            for testsuite in test_grp_report:
                if testsuite.failed:
                    if (
                        isinstance(testsuite, TestGroupReport)
                        and testsuite.category == ReportCategories.SYNTHESIZED
                    ):
                        failed_tests.add(test_grp_report.name)
                        break
                    if (
                        self.cfg.failed_tests_level
                        == FailedTestLevel.TESTSUITE
                    ):
                        failed_tests.add(
                            f"{test_grp_report.definition_name}:{testsuite.name}"
                        )
                        continue
                    for testcase in testsuite:
                        if not testcase.failed:
                            continue
                        if testcase.category == ReportCategories.SYNTHESIZED:
                            failed_tests.add(
                                f"{test_grp_report.definition_name}:{testsuite.name}"
                            )
                            break
                        if isinstance(testcase, TestGroupReport):
                            # Parametric test case
                            for param_case in testcase:
                                if param_case.failed:
                                    failed_tests.add(
                                        f"{test_grp_report.definition_name}:"
                                        f"{testsuite.name}:"
                                        f"{param_case.name}"
                                    )
                        else:
                            failed_tests.add(
                                f"{test_grp_report.definition_name}:{testsuite.name}:{testcase.name}"
                            )

        failed_test_path.parent.mkdir(exist_ok=True)
        with failed_test_path.open("w") as failed_tests_file:
            for test in sorted(failed_tests):
                failed_tests_file.write(f"{test}\n")

        self.logger.user_info(
            "Failed tests has been saved in %s", failed_test_path
        )
        return
