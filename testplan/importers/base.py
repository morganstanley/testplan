"""
Implements base importer classes.
"""

from abc import ABCMeta, abstractmethod
from typing import Any, TypeVar, Generic, List, Optional

from testplan.report import TestGroupReport, TestReport


class ImportedResult(metaclass=ABCMeta):
    """
    Base class for imported results.
    """

    @abstractmethod
    def as_test_report(self) -> TestReport:
        raise NotImplementedError

    @abstractmethod
    def category(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def results(self) -> List[TestGroupReport]:
        raise NotImplementedError


class ResultImporter(metaclass=ABCMeta):
    """
    Base class for result importer.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def import_result(self) -> ImportedResult:
        raise NotImplementedError


T = TypeVar("T")


class ThreePhaseFileImporter(ResultImporter, Generic[T]):
    """
    ResultImporter subclass that implements a three-phase file importer.
    """

    def __init__(
        self,
        path: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        :param path: path to source file
        :param name: name of the generated in-memory testplan
        :param description: description of generated test result
        """
        self.path = path
        self.name = name or path
        self.description = description or f"Report imported from {path}"

    def import_result(self) -> ImportedResult:
        """
        Imports result from the source file.
        """
        raw_data = self._read_data(self.path)
        processed_data = self._process_data(raw_data)
        return self._create_result(raw_data, processed_data)

    # TODO: this looks like a static method except for CPPUnitResultImporter
    #       maybe we can use self.path only?
    @abstractmethod
    def _read_data(self, path: str) -> T:
        """
        Reads result from the source file.

        :param path: path to source file
        """
        raise NotImplementedError

    @abstractmethod
    def _process_data(self, data: T) -> List[TestGroupReport]:
        """
        Processes data read from the source file.

        :param data: raw data as read by the importer
        """
        raise NotImplementedError

    # TODO: raw_data, apparently, is never used maybe we can do without it
    @abstractmethod
    def _create_result(
        self, raw_data: T, processed_data: List[TestGroupReport]
    ) -> ImportedResult:
        """
        Creates in-memory imported result from processed data.

        :param raw_data: raw data as read by the importer
        :param processed_data: list of data as processed by the importer
        """
        raise NotImplementedError
