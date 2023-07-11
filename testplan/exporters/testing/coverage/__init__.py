"""
Coverage data related exporter.
"""


import pathlib
import sys
from collections import OrderedDict
from contextlib import contextmanager
from typing import Dict, Generator, Mapping, TextIO, Tuple, Optional

from testplan.common.exporters import (
    ExporterConfig,
    ExportContext,
    _verify_export_context,
)
from testplan.exporters.testing.base import Exporter
from testplan.report.testing.base import (
    TestCaseReport,
    TestGroupReport,
    TestReport,
)


class CoveredTestsExporter(Exporter):
    """
    Exporting covered tests to somewhere on this planet.
    """

    CONFIG = ExporterConfig

    def __init__(self, name: str = "Covered Tests Exporter", **options):
        super(CoveredTestsExporter, self).__init__(name=name, **options)

    def export(
        self,
        source: TestReport,
        export_context: Optional[ExportContext] = None,
    ) -> Optional[Dict]:
        """
        Exports report coverage data.

        :param: source: Testplan report to export
        :param: export_context: information about other exporters
        :return: ExporterResult object containing information about the actual exporter object and its possible output
        """

        export_context = _verify_export_context(
            exporter=self, export_context=export_context
        )
        if len(source):
            # here we use an OrderedDict as an ordered set
            results = OrderedDict()
            for entry in source.entries:
                if isinstance(entry, TestGroupReport):
                    self._append_covered_group_n_case(entry, [], results)
            if results:
                with _custom_open(self.cfg.tracing_tests_output) as (
                    f,
                    fn,
                ):
                    self.logger.user_info(f"Impacted tests output to {fn}.")
                    for k in results.keys():
                        f.write(":".join(k) + "\n")
                result = {"coverage": self.cfg.tracing_tests_output}
                return result
            self.logger.user_info("No impacted tests found.")
            return None
        return None

    def _append_covered_group_n_case(
        self,
        report: TestGroupReport,
        path: Tuple[str, ...],
        result: Mapping[Tuple[str, ...], None],
    ):
        """
        Recursively add test group or test case with covered_lines set to
        the result ordered set.

        Here we use an OrderedDict as an ordered set.
        """
        curr_path = (*path, report.name)
        if report.covered_lines:
            result[curr_path] = None
        for entry in report.entries:
            if isinstance(entry, TestGroupReport):
                self._append_covered_group_n_case(entry, curr_path, result)
            elif isinstance(entry, TestCaseReport):
                if entry.covered_lines:
                    result[(*curr_path, entry.name)] = None


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
