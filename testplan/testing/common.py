import re
from dataclasses import dataclass
from enum import IntEnum, auto
from itertools import product
from typing import List, Optional

from typing_extensions import Self

from testplan.report.testing import Status

TEST_PART_PATTERN_FORMAT_STRING = "{} - part({}/{})"

# NOTE: no rigorous check performed before passed to fnmatch
TEST_PART_PATTERN_REGEX = re.compile(
    r"^(.*) - part\(([\!0-9\[\]\?\*]+)/([\!0-9\[\]\?\*]+)\)$"
)


class _SkipStrategyOffset(IntEnum):
    NONE = auto()  # empty
    CASES = auto()
    SUITES = auto()
    TESTS = auto()  # universe


@dataclass
class SkipStrategy:
    offset: _SkipStrategyOffset
    threshold: Status

    @classmethod
    def noop(cls) -> Self:
        return cls(_SkipStrategyOffset.NONE, Status.NONE)

    def to_option(self) -> str:
        if not self:
            return "None"
        return f"{self.offset.name.lower()}-on-{self.threshold.to_json_compatible()}"

    @classmethod
    def from_option(cls, option: str) -> Self:
        vals = cls.all_options()
        if option not in vals:
            raise ValueError(
                f"invalid option for ``SkipStrategy``, valid values are {vals}."
            )
        sib, st = option.split("-on-")
        return cls(
            _SkipStrategyOffset[sib.upper()], Status.from_json_compatible(st)
        )

    @classmethod
    def from_option_or_none(cls, maybe_option: Optional[str]) -> Self:
        if maybe_option is None:
            return cls.noop()
        if isinstance(maybe_option, str):
            return cls.from_option(maybe_option)
        raise TypeError(
            f"Invalid type, expecting None or a string in {cls.all_options()}."
        )

    @classmethod
    def all_options(cls) -> List[str]:
        return list(
            map(
                lambda x: "-on-".join(x),
                product(["cases", "suites", "tests"], ["failed", "error"]),
            )
        )

    def should_skip_rest_cases(self, case_status: Status):
        return (
            self.offset >= _SkipStrategyOffset.CASES
            and case_status <= self.threshold
        )

    def should_skip_rest_suites(self, suite_status: Status):
        return (
            self.offset >= _SkipStrategyOffset.SUITES
            and suite_status <= self.threshold
        )

    def should_skip_rest_tests(self, test_status: Status):
        return (
            self.offset >= _SkipStrategyOffset.TESTS
            and test_status <= self.threshold
        )

    def union(self, other: Self) -> Self:
        def _cmp(x: Status, y: Status):
            try:
                r = x < y
            except TypeError:
                return x.normalised()
            else:
                return x if r else y

        return self.__class__(
            max(self.offset, other.offset),
            _cmp(self.threshold, other.threshold),
        )

    def __bool__(self) -> bool:
        return self.offset > _SkipStrategyOffset.NONE and bool(self.threshold)

    def to_skip_reason(self) -> str:
        if not self:
            raise RuntimeError("``to_skip_reason`` shouldn't be invoked here")
        return (
            f"previously reported {self.threshold.name.lower()} meeting the "
            "skip condition, which is configured by skip strategy"
        )
