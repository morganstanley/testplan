"""
Implements base action types.
"""

from abc import ABCMeta, abstractmethod
from typing import Iterable

from testplan.report import TestReport


class ParseSingleAction(metaclass=ABCMeta):
    """
    Base class for single parser action.
    """

    @abstractmethod
    def __call__(self) -> TestReport:
        raise NotImplementedError


class ParseMultipleAction(metaclass=ABCMeta):
    """
    Base class for multiple parser actions.
    """

    @abstractmethod
    def __call__(self) -> Iterable[TestReport]:
        raise NotImplementedError


class ProcessResultAction(metaclass=ABCMeta):
    """
    Base class for result processing action.
    """

    @abstractmethod
    def __call__(self, result: TestReport) -> TestReport:
        raise NotImplementedError
