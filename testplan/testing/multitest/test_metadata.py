from dataclasses import dataclass, field
from inspect import getsourcefile, getsourcelines, isclass, unwrap
from typing import List, Optional, Union

LOCATION_METADATA_ATTRIBUTE = "__location_metadata__"


@dataclass
class LocationMetadata:
    object_name: str
    file: str
    line_no: int

    @classmethod
    def from_object(cls, obj: object) -> Optional["LocationMetadata"]:
        # some cases where testcases /suites generated on the fly user can provide meaningfull metadata
        # with attaching one to the object
        if hasattr(obj, LOCATION_METADATA_ATTRIBUTE):
            return getattr(obj, LOCATION_METADATA_ATTRIBUTE)  # type: ignore[no-any-return]
        try:
            object_name = obj.__name__  # type: ignore[attr-defined]
            # ``getsourcelines`` follows ``functools.wraps``'s ``__wrapped__``
            # chain but ``getsourcefile`` does not, so resolve both from the
            # same unwrapped target.
            target = obj if isclass(obj) else unwrap(obj)  # type: ignore[arg-type]
            file = getsourcefile(target)
            _, line_no = getsourcelines(target)
        except Exception:
            return None  # we do best effort here
        else:
            return cls(object_name, file or "", line_no)


@dataclass
class TestCaseStaticMetadata:
    location: Optional[LocationMetadata]


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
    location: Optional[LocationMetadata]


@dataclass
class TestSuiteMetadata(TestSuiteStaticMetadata, BasicInfo):
    test_cases: List[TestCaseMetadata]


@dataclass
class TestMetadata(BasicInfo):
    test_suites: List[TestSuiteMetadata]

    def __post_init__(self) -> None:
        # computing ids propagating parent ids, this assume that the metadat is used in an
        # immutable manner. If it is used in a mutable way compute_ids need to be called to
        # recalculate ids for all siblings
        self.compute_ids()

    def compute_ids(self) -> None:
        self.id = self.name
        for suite in self.test_suites:
            suite.id = f"{self.id}:{suite.name}"
            for tc in suite.test_cases:
                tc.id = f"{suite.id}:{tc.name}"


@dataclass
class TestPlanMetadata(BasicInfo):
    tests: List[TestMetadata]
