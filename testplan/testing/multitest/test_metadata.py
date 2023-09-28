from dataclasses import dataclass, field
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
class BasicInfo:
    name: str
    description: Union[str, None]
    id: Union[str, None] = field(default=None, init=False)


@dataclass
class TestCaseMetadata(TestCaseStaticMetadata, BasicInfo):
    pass


@dataclass
class TestSuiteStaticMetadata:

    location: LocationMetadata


@dataclass
class TestSuiteMetadata(TestSuiteStaticMetadata, BasicInfo):

    test_cases: List[TestCaseMetadata]


@dataclass
class TestMetadata(BasicInfo):
    test_suites: List[TestSuiteMetadata]

    def __post_init__(self):
        # computing ids propagating parent ids, this assume that the metadat is used in an
        # immutable manner. If it is used in a mutable way compute_ids need to be called to
        # recalculate ids for all siblings
        self.compute_ids()

    def compute_ids(self):
        self.id = self.name
        for suite in self.test_suites:
            suite.id = f"{self.id}:{suite.name}"
            for tc in suite.test_cases:
                tc.id = f"{suite.id}:{tc.name}"


@dataclass
class TestPlanMetadata(BasicInfo):
    tests: List[TestMetadata]
