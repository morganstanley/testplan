try:
    from typing import Self  # >= 3.11
except ImportError:
    from typing_extensions import Self  # < 3.11

from schema import And

from testplan.common.config.base import ConfigOption
from testplan.common.entity import Entity
from testplan.common.entity.base import EntityConfig
from testplan.report.testing.base import Status, TestReport


class ReportingFilterConfig(EntityConfig):
    @classmethod
    def get_options(cls):
        # we only handle simple situations right now,
        # see docstring for ReportingFilter
        return {
            ConfigOption("sign"): bool,
            ConfigOption("flags"): And(
                set,
                lambda l: all(isinstance(x, str) for x in l),
            ),
        }


class ReportingFilter(Entity):
    """
    Testcase-level report filter based on their execution result.
    Use upper-case letters to include testcases of certain result,
    use lower-case letters to exclude them. Using upper-case and lower-
    case together is not permitted.
    """

    CONFIG = ReportingFilterConfig
    OPTION_MAPPER = {
        "E": Status.ERROR,
        "F": Status.FAILED,
        "I": Status.INCOMPLETE,
        "P": Status.PASSED,
        "S": Status.SKIPPED,
        "U": Status.UNSTABLE,
        "X": Status.UNKNOWN,
        "A": Status.XFAIL,
        "B": Status.XPASS,
        "C": Status.XPASS_STRICT,
    }

    def __call__(self, report: TestReport) -> TestReport:
        """
        Execute self on TestReport.
        """
        if self.cfg.sign:
            func = lambda x: any(f == x.status for f in self.cfg.flags)
        else:
            func = lambda x: all(f != x.status for f in self.cfg.flags)
        return report.filter_cases(func, is_root=True)

    @classmethod
    def parse(cls, cli_options: str) -> Self:
        flags = set()
        sign = cli_options[0].isupper()
        for o in cli_options:
            if sign != o.isupper():
                raise ValueError(
                    "Invalid filter presented, only all upper case letters "
                    "or all lower case letters is accepted."
                )
            try:
                flags.add(cls.OPTION_MAPPER.get(o.upper()))
            except KeyError as e:
                raise ValueError("Invalid option specified.") from e

        return cls(sign=sign, flags=flags)
