"""
Implements base action types.
"""

from typing import Iterable

from testplan.report import TestReport


class ParseSingleAction:
    """
    Base class for single parser action.
    """

    def __call__(self) -> TestReport:
        raise NotImplementedError


class ParseMultipleAction:
    """
    Base class for multiple parser actions.
    """

    def __call__(self) -> Iterable[TestReport]:
        raise NotImplementedError


class ProcessResultAction:
    """
    Base class for result processing action.
    """

    def __call__(self, result: TestReport) -> TestReport:
        raise NotImplementedError
