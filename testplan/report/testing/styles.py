"""
Styling enums & flags for rendering test output.

Test report outputs will use common styling flags to render the test data
on different outputs (e.g. console, pdf, web), using custom information
levels (multitests, suites, tescases, assrtions, assertion details).

We also allow separate styling for passing and failing tests, so it is
possible to get assertion details for failing tests but just return high
level multitest pass/fail status for passing test groups.
"""

import os
from enum import Enum, unique

from testplan.common.utils.parser import ArgMixin


@unique
class StyleEnum(ArgMixin, Enum):
    """
    Incremental output levels, this will be used by
    `StyleFlag` class to set styling flags like:

        * display_result = True
        * display_multitest = False

    Note: Multiple inheritance seems to break with IntEnum.
    """

    RESULT = 0
    TEST = 1
    TESTSUITE = 2
    TESTCASE = 3
    ASSERTION = 4
    ASSERTION_DETAIL = 5


class StyleFlag:
    """
    This class generates styling attributes using the given output level.
    It will use the incremental values of StyleEnum to set its
    display flag attributes.

    This gives us a nice flag with clear attributes to work with when
    we implement the rendering logic.

    Usage:

        StyleFlag(StyleEnum.TESTCASE)

    Alternative Usage:

        StyleFlag('testcase')

    Produces:

        StyleFlag

            * display_result = True
            * display_test = True
            * display_testsuite = True
            * display_testcase = True
            * display_assertion = False
            * display_assertion_detail = False
    """

    attrs = ["display_{}".format(enm.name.lower()) for enm in StyleEnum]

    def __init__(self, level):

        if isinstance(level, str):
            self.label = level
        elif isinstance(level, Enum):
            self.label = StyleEnum.enum_to_str(level)
        else:
            raise TypeError("Invalid type: {}".format(type(level)))

        for enm, attr_name in zip(StyleEnum, self.attrs):
            setattr(self, attr_name, enm.value <= self.level.value)

    @property
    def level(self):
        """
        Need this as a property rather than attribute,
        so we can pickle StyleFlag objects
        """
        return StyleEnum.str_to_enum(self.label)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.label)

    def __str__(self):
        ret = [repr(self)] + [
            "\t{}: {}".format(attr, getattr(self, attr)) for attr in self.attrs
        ]
        return os.linesep.join(ret)

    def __eq__(self, other):
        return all(
            getattr(self, attr) == getattr(other, attr) for attr in self.attrs
        )

    def __gt__(self, other):
        return self.level.value > other.level.value


class Style:
    """
    Container for StyleFlag objects, we will make use of
    2 StyleFlag objects for passing / failing test result rendering.

    e.g. Render passing multitests, but render
    failing multitest & suite & testcases.
    """

    def __init__(self, passing, failing):
        self.passing = StyleFlag(passing)
        self.failing = StyleFlag(failing)

    def __repr__(self):
        return "{}(passing='{}', failing='{}')".format(
            self.__class__.__name__, self.passing.label, self.failing.label
        )

    def get_style(self, passing=True):
        return self.passing if passing else self.failing

    def __eq__(self, other):
        return self.passing == other.passing and self.failing == other.failing


class StyleArg(ArgMixin, Enum):
    """
    Argparse utility that gives us StyleFlag tuples for matching
    argument values. This will be used for shortcut styling of
    outputs (e.g. stdout, pdf) from cmdline args.

    For fine tuning how the output is rendered, the style object
    must be passed to related renderer programmatically.
    """

    RESULT_ONLY = Style(passing=StyleEnum.RESULT, failing=StyleEnum.RESULT)

    SUMMARY = Style(passing=StyleEnum.TEST, failing=StyleEnum.TEST)

    EXTENDED_SUMMARY = Style(
        passing=StyleEnum.TESTCASE, failing=StyleEnum.ASSERTION_DETAIL
    )

    DETAILED = Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    )

    @classmethod
    def get_descriptions(cls):
        """
        Description mapping for enums, will be rendered
        via --help command.
        """
        return {
            cls.RESULT_ONLY: "Display only root level pass/fail status.",
            cls.SUMMARY: "Display top level (e.g. multitest)"
            " pass/fail status .",
            cls.EXTENDED_SUMMARY: "Display assertion details for failing tests,"
            " testcase level statuses for the rest.",
            cls.DETAILED: "Display details of all tests & assertions.",
        }
