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
class SkipStrategy:
    case_comparable: Status
    suite_comparable: Status
    test_comparable: Status

    @classmethod
    def noop(cls) -> Self:
        return cls(Status.BOTTOM, Status.BOTTOM, Status.BOTTOM)

    @classmethod
    def from_option(cls, option: str) -> Self:
        vals = cls.all_options()
        if option not in vals:
            raise ValueError(
                f"invalid option for ``SkipStrategy``, valid values are {vals}."
            )
        sib, st = option.split("-on-")
        st = Status(st)
        r = cls.noop()
        r.case_comparable = st
        if sib == "suites":
            r.suite_comparable = st
        if sib == "tests":
            r.suite_comparable = st
            r.test_comparable = st
        return r

    @classmethod
    def from_option_or_none(cls, maybe_option: Optional[str]) -> Self:
        if isinstance(maybe_option, str):
            return cls.from_option(maybe_option)
        if maybe_option is None:
            return cls.noop()
        raise ValueError(
            f"Invalid value, expecting None or a string in {cls.all_options()}."
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
        return case_status <= self.case_comparable

    def should_skip_rest_suites(self, suite_status: Status):
        return suite_status <= self.suite_comparable

    def should_skip_rest_tests(self, test_status: Status):
        return test_status <= self.test_comparable

    def union(self, other: Self) -> Self:
        def _cmp(x: Status, y: Status):
            try:
                r = x > y
            except TypeError:
                return x.normalised()
            else:
                return x if r else y

        return self.__class__(
            _cmp(self.case_comparable, other.case_comparable),
            _cmp(self.suite_comparable, other.suite_comparable),
            _cmp(self.test_comparable, other.test_comparable),
        )

    def __bool__(self) -> bool:
        return any(
            map(
                bool,
                [
                    self.case_comparable,
                    self.suite_comparable,
                    self.test_comparable,
                ],
            )
        )
