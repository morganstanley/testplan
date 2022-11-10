"""
Easy-to-use wrapper around Coverage.py for Python source code tracing
"""

from contextlib import contextmanager
from typing import Dict, List, Optional, Union

from coverage import Coverage, CoverageData
from testplan.report.testing.base import TestCaseReport, TestGroupReport


class Watcher:
    def __init__(self):
        self._watching_lines: Optional[Dict[str, List[int]]] = None
        self._tracer: Optional[Coverage] = None

    def set_watching_lines(self, watching_lines: Dict[str, List[int]]):
        if watching_lines:
            self._watching_lines = watching_lines
            # we explicitly disable writing coverage data to file
            self._tracer = Coverage(
                data_file=None, include=[*watching_lines.keys()]
            )

    def _get_common_lines(self, data: CoverageData) -> Dict[str, List[int]]:
        r = {}
        for covered_file in data.measured_files():
            for f_name, f_lines in self._watching_lines.items():
                if covered_file.endswith(f_name):
                    common_lines = set(data.lines(covered_file)).intersection(
                        f_lines
                    )
                    if common_lines:
                        r[f_name] = sorted(list(common_lines))
        return r

    @contextmanager
    def save_covered_lines_to(
        self, report: Union[TestCaseReport, TestGroupReport]
    ):
        if self._tracer is None:
            yield
        else:
            self._tracer.erase()
            self._tracer.start()
            try:
                yield
            finally:
                # exception shall bubble out
                self._tracer.stop()
                data = self._tracer.get_data()
                if data is not None and data.measured_files():
                    report.covered_lines = self._get_common_lines(data) or None
