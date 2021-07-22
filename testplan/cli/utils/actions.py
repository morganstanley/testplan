from typing import Iterable

from testplan.report import TestReport


class ParseSingleAction:
    def __call__(self) -> TestReport:
        pass


class ParseMultipleAction:
    def __call__(self) -> Iterable[TestReport]:
        pass


class ProcessResultAction:
    def __call__(self, result: TestReport) -> TestReport:
        pass
