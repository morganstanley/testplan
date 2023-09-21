from dataclasses import dataclass
from inspect import getsourcefile, getsourcelines
from typing import List, Optional, Union


@dataclass
class LocationMetadata:

    object_name: str
    file: str
    line_no: int

    @classmethod
    def from_object(cls, obj):
        object_name = obj.__name__
        file = getsourcefile(obj)
        _, line_no = getsourcelines(obj)
        return cls(object_name, file, line_no)


@dataclass
class TestCaseStaticMetadata:
    location: LocationMetadata


@dataclass
class TestCaseMetadata(TestCaseStaticMetadata):
    name: str
    description: Union[str, None]


@dataclass
class TestSuiteStaticMetadata:

    location: LocationMetadata


@dataclass
class TestSuiteMetadata(TestSuiteStaticMetadata):

    name: str
    description: Union[str, None]
    test_cases: List[TestCaseMetadata]


@dataclass
class TestMetadata:
    name: str
    description: str
    test_suites: List[TestSuiteMetadata]


@dataclass
class TestPlanMetadata:
    name: str
    description: str
    tests: List[TestMetadata]
