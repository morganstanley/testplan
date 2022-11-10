"""
Coverage data related exporter.
"""


import pathlib
import sys
from contextlib import contextmanager
from enum import IntEnum, auto
from typing import Generator, OrderedDict, TextIO, Tuple

from testplan.common.exporters import ExporterConfig
from testplan.exporters.testing.base import Exporter
from testplan.report.testing.base import (
    TestCaseReport,
    TestGroupReport,
    TestReport,
)


class ExportingCoverage(IntEnum):
    # more type might be added later
    ExportTestsAsPattern = auto()


class CoverageExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class: `CoverageExporter <testplan.exporters.testing.coverage.CoverageExporter>`
    object.
    """

    @classmethod
    def get_options(cls):
        return {"coverage_export_type": ExportingCoverage}


class CoverageExporter(Exporter):
    """
    Exporter focusing on coverage data.
    """

    CONFIG = CoverageExporterConfig

    def __init__(self, name: str = "Custom File Exporter", **options):
        super(CoverageExporter, self).__init__(name=name, **options)

    def export(self, report: TestReport):
        if len(report):
            if (
                self.cfg.coverage_export_type
                == ExportingCoverage.ExportTestsAsPattern
            ):
                results = OrderedDict()
                for mt_entry in report.entries:
                    if isinstance(mt_entry, TestGroupReport):
                        if mt_entry.covered_lines:
                            results[(mt_entry.name,)] = None
                            continue
                        for ts_entry in mt_entry.entries:
                            if isinstance(ts_entry, TestGroupReport):
                                if ts_entry.covered_lines:
                                    results[
                                        (mt_entry.name, ts_entry.name)
                                    ] = None
                                    continue
                                for tc_entry in ts_entry.entries:
                                    if isinstance(tc_entry, TestCaseReport):
                                        if tc_entry.covered_lines:
                                            results[
                                                (
                                                    mt_entry.name,
                                                    ts_entry.name,
                                                    tc_entry.name,
                                                )
                                            ] = None
                if results:
                    with _custom_open(self.cfg.impacted_tests_output) as (
                        f,
                        fn,
                    ):
                        self.logger.exporter_info(
                            f"Impacted tests output to {fn}."
                        )
                        for k in results.keys():
                            f.write(":".join(k) + "\n")
                    return self.cfg.impacted_tests_output
        self.logger.exporter_info("No impacted tests found.")
        return None


@contextmanager
def _custom_open(path: str) -> Generator[Tuple[TextIO, str], None, None]:
    """
    Custom file context manager that treat "-" as standard output.
    """

    if path == "-":
        fh = sys.stdout
        fn = "Standard Output"
    else:
        file_path = pathlib.Path(path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(file_path, "w")
        fn = str(file_path)
    try:
        yield fh, fn
    finally:
        if fh != sys.stdout:
            fh.close()
