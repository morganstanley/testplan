from typing import List, NamedTuple, Union

from schema import And, Or
from typing_extensions import Self

from testplan.common.config.base import ConfigOption
from testplan.common.entity import Entity
from testplan.common.entity.base import EntityConfig
from testplan.report.testing.base import Status, TestReport


class PositiveFlag(NamedTuple):
    s: Status

    def test_report(self, report: TestReport) -> bool:
        return self.s == report.status


class NegativeFlag(NamedTuple):
    s: Status

    def test_report(self, report: TestReport) -> bool:
        return self.s != report.status


class ReportingFilterConfig(EntityConfig):
    @classmethod
    def get_options(cls):
        return {
            # we only handle simple situations right now
            ConfigOption("flags"): Or(
                And(
                    list,
                    lambda l: len(l),
                    lambda l: all(isinstance(x, PositiveFlag) for x in l),
                ),
                And(
                    list,
                    lambda l: len(l),
                    lambda l: all(isinstance(x, NegativeFlag) for x in l),
                ),
            )
        }


class ReportingFilter(Entity):
    CONFIG = ReportingFilterConfig
    OPTION_MAPPER = {
        "E": PositiveFlag(Status.ERROR),
        "F": PositiveFlag(Status.FAILED),
        "I": PositiveFlag(Status.INCOMPLETE),
        "P": PositiveFlag(Status.PASSED),
        "S": PositiveFlag(Status.SKIPPED),
        "U": PositiveFlag(Status.UNSTABLE),
        "X": PositiveFlag(Status.UNKNOWN),
        "A": PositiveFlag(Status.XFAIL),
        "B": PositiveFlag(Status.XPASS),
        "C": PositiveFlag(Status.XPASS_STRICT),
        "e": NegativeFlag(Status.ERROR),
        "f": NegativeFlag(Status.FAILED),
        "i": NegativeFlag(Status.INCOMPLETE),
        "p": NegativeFlag(Status.PASSED),
        "s": NegativeFlag(Status.SKIPPED),
        "u": NegativeFlag(Status.UNSTABLE),
        "x": NegativeFlag(Status.UNKNOWN),
        "a": NegativeFlag(Status.XFAIL),
        "b": NegativeFlag(Status.XPASS),
        "c": NegativeFlag(Status.XPASS_STRICT),
    }

    def __init__(self, flags: Union[List[PositiveFlag], List[NegativeFlag]]):
        super(ReportingFilter, self).__init__(flags=flags)

    def __call__(self, report: TestReport) -> TestReport:
        """
        Execute self on TestReport.
        """
        if isinstance(self.cfg.flags[0], PositiveFlag):
            func = lambda x: any(f.test_report(x) for f in self.cfg.flags)
        else:
            func = lambda x: all(f.test_report(x) for f in self.cfg.flags)
        return report.filter_cases(func, is_root=True)

    @classmethod
    def parse(cls, cli_options: str) -> Self:
        flags = []
        for o in cli_options:
            try:
                flags.append(cls.OPTION_MAPPER.get(o))
            except KeyError as e:
                raise ValueError("invalid option specified") from e

        return cls(flags)
