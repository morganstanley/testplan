"""
Easy-to-use wrapper around Coverage.py for Python source code tracing
"""

from contextlib import contextmanager
from logging import Logger
from typing import Dict, List, Optional, Set, Union, Generator

try:
    from typing import Literal  # >= 3.8
except ImportError:
    from typing_extensions import Literal  # < 3.8

from coverage import Coverage, CoverageData

from testplan.common.utils.logger import Loggable
from testplan.report.testing.base import TestCaseReport, TestGroupReport


class Watcher(Loggable):
    """
    Utility class for testcase execution tracing.

    NOTE: We should use absolute path of files since matching by part of path
    NOTE: might include unwanted files for tracing, i.e. "*a.py" will match on
    NOTE: both a.py and some/deep/path/a.py. If the input files are absolute
    NOTE: paths, we can do exact match for local runners and replace local
    NOTE: workspace path with remote workspace path before doing exact match
    NOTE: for remote runners. However, currently we cannot simply interpret the
    NOTE: relative paths as paths under current working directory, and we don't
    NOTE: have a global workspace. Here we just use matching by part of path as
    NOTE: a workaround.
    """

    def __init__(self) -> None:
        super().__init__()
        self._disabled: bool = False
        self._watching_lines: Optional[
            Dict[str, Union[List[int], Literal["*"]]]
        ] = None
        self._tracer: Optional[Coverage] = None

    def set_watching_lines(
        self, watching_lines: Dict[str, Union[List[int], Literal["*"]]]
    ) -> None:
        if watching_lines:
            self._watching_lines = watching_lines
            self.logger.debug(
                "Now tracing the following files: %s",
                list(self._watching_lines.keys()),
            )
            # we explicitly disable writing coverage data to file
            self._tracer = Coverage(
                data_file=None,
                include=[f"*{k}" for k in self._watching_lines.keys()],
            )

    def _get_common_lines(self, data: CoverageData) -> Dict[str, Set[int]]:
        r = {}
        for covered_file in data.measured_files():
            for f_name, f_lines in self._watching_lines.items():
                if covered_file.endswith(f_name):
                    covered_lines = set(data.lines(covered_file))
                    if isinstance(f_lines, str) and f_lines == "*":
                        common_lines = covered_lines
                    else:
                        common_lines = covered_lines.intersection(f_lines)
                    if common_lines:
                        r[f_name] = common_lines
        return r

    @contextmanager
    def disabled(
        self, logger: Optional[Logger] = None, reason: Optional[str] = None
    ) -> Generator:
        """
        Temporarily disable watcher due to the passed in reason,
        or some unknown reason.
        """
        if self._tracer is None:
            yield
        else:
            prev_disabled = self._disabled
            self._disabled = True
            logger.warning(reason)
            try:
                yield
            finally:
                self._disabled = prev_disabled

    @contextmanager
    def save_covered_lines_to(
        self, report: Union[TestCaseReport, TestGroupReport]
    ) -> Generator:
        """
        Context manager that enables source code tracing
        and covered lines data saving to report at exit.
        """
        if self._tracer is None or self._disabled:
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
                    common_lines = self._get_common_lines(data)
                    # set or merge the common lines
                    if len(common_lines):
                        if report.covered_lines is None:
                            report.covered_lines = common_lines
                        else:
                            for k, v in common_lines.items():
                                report.covered_lines[
                                    k
                                ] = report.covered_lines.get(k, set()).union(
                                    set(v)
                                )
