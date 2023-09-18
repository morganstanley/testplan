from dataclasses import dataclass
from inspect import getsourcefile, getsourcelines
from typing import List


@dataclass
class LocationMetadata:

    file: str
    line_no: int

    @classmethod
    def from_object(cls, func):
        file = getsourcefile(func)
        _, line_no = getsourcelines(func)
        return cls(file, line_no)


@dataclass
class TestCaseMetadata:

    name: str
    location: LocationMetadata


@dataclass
class TestSuiteMetadata:

    name: str
    location: LocationMetadata


@dataclass
class ExtendedTestSuiteMetadata(TestSuiteMetadata):
    test_cases: List[TestCaseMetadata]


@dataclass
class TestMetadata:
    name: str
    test_suites: List[ExtendedTestSuiteMetadata]


@dataclass
class TestPlanMetadata:
    name: str
    tests: List[TestMetadata]
