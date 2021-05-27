from typing import TypeVar, Generic, List

from testplan.report import TestGroupReport, TestReport


class ImportedResult:
    def as_test_report(self) -> TestReport:
        raise NotImplementedError

    def category(self) -> str:
        raise NotImplementedError

    def results(self) -> (List[TestGroupReport]):
        raise NotImplementedError


class ResultImporter:
    def import_result(self) -> ImportedResult:
        raise NotImplementedError


T = TypeVar("T")


class ThreePhaseFileImporter(ResultImporter, Generic[T]):
    def __init__(self, path: str, name: str = None, description: str = None):

        self.path = path
        self.name = name or path
        self.description = description or f"Report imported from {path}"

    def import_result(self) -> ImportedResult:
        raw_data = self._read_data(self.path)
        processed_data = self._process_data(raw_data)
        return self._create_result(raw_data, processed_data)

    def _read_data(self, path) -> T:
        raise NotImplementedError

    def _process_data(self, data: T) -> List[TestGroupReport]:
        raise NotImplementedError

    def _create_result(
        self, raw_data: T, processed_data: List[TestGroupReport]
    ) -> ImportedResult:
        raise NotImplementedError
