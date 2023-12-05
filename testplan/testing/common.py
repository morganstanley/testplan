import re
from dataclasses import dataclass
from itertools import product
from typing import List, Optional

from typing_extensions import Self

from testplan.report.testing import Status

TEST_PART_PATTERN_FORMAT_STRING = "{} - part({}/{})"

# NOTE: no rigorous check performed before passed to fnmatch
TEST_PART_PATTERN_REGEX = re.compile(
    r"^(.*) - part\(([\!0-9\[\]\?\*]+)/([\!0-9\[\]\?\*]+)\)$"
)


@dataclass
class TestBreakerThres:
    plan_level: Status
    test_level: Status
    suite_level: Status

    @classmethod
    def null(cls) -> Self:
        return cls(Status(None), Status(None), Status(None))

    @classmethod
    def parse(cls, option: str) -> Self:
        tl, sl = option.split("-on-")
        s = Status(sl)
        r = cls.null()
        r.suite_level = s
        if tl == "test":
            r.test_level = s
        elif tl == "plan":
            r.test_level = s
            r.plan_level = s
        return r

    @classmethod
    def reps(cls) -> List[str]:
        return list(
            map(
                lambda x: "-on-".join(x),
                product(["suite", "test", "plan"], ["failed", "error"]),
            )
        )

    def __bool__(self):
        return (
            bool(self.plan_level)
            or bool(self.test_level)
            or bool(self.suite_level)
        )
