"""
Coverage data related exporter.
"""


import pathlib
import sys
from collections import OrderedDict
from contextlib import contextmanager
from typing import Dict, Generator, Mapping, Optional, TextIO, Tuple

from testplan.common.exporters import (
    ExportContext,
    ExporterConfig,
    verify_export_context,
)
from testplan.exporters.testing.base import Exporter
from testplan.report.testing.base import (
    ReportCategories,
    TestGroupReport,
    TestReport,
)
from testplan.testing.common import TEST_PART_PATTERN_FORMAT_STRING


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
        :return: dictionary containing the possible output
        """

        export_context = verify_export_context(
            exporter=self, export_context=export_context
        )
        if len(source):
            # here we use an OrderedDict as an ordered set
            results = OrderedDict()
            for entry in source.entries:
                if (
                    isinstance(entry, TestGroupReport)
                    and entry.category == ReportCategories.MULTITEST
                ):
                    self._append_mt_coverage(entry, results)
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

    def _append_mt_coverage(
        self,
        report: TestGroupReport,
        result: Mapping[Tuple[str, ...], None],
    ):
        """
        Add test entity with covered_lines set to the result ordered set.

        Here we use an OrderedDict as an ordered set.
        """

        if report.part is not None:
            mt_pat = TEST_PART_PATTERN_FORMAT_STRING.format(
                report.definition_name, report.part[0], report.part[1]
            )
        else:
            mt_pat = report.definition_name

        if report.covered_lines:
            result[(mt_pat,)] = None
        for st in report.entries:
            if st.covered_lines:
                result[(mt_pat, st.definition_name)] = None
            for tc in st.entries:
                if tc.category == ReportCategories.PARAMETRIZATION:
                    for sub_tc in tc.entries:
                        if sub_tc.covered_lines:
                            result[
                                (
                                    mt_pat,
                                    st.definition_name,
                                    sub_tc.definition_name,
                                )
                            ] = None
                elif tc.covered_lines:
                    result[
                        (mt_pat, st.definition_name, tc.definition_name)
                    ] = None


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
