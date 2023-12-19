from testplan.report.testing.base import Status
from testplan.testing.common import (
    TEST_PART_PATTERN_FORMAT_STRING,
    TEST_PART_PATTERN_REGEX,
    SkipStrategy,
)

SKIP_STRATEGY_OPTIONS_ON_PAPER = {
    "tests-on-error",
    "tests-on-failed",
    "suites-on-error",
    "suites-on-failed",
    "cases-on-error",
    "cases-on-failed",
}


def test_part_pattern():
    mt_name = TEST_PART_PATTERN_FORMAT_STRING.format("MT", 0, 2)
    m = TEST_PART_PATTERN_REGEX.match(mt_name)
    assert m.group(1) == "MT"
    assert m.group(2) == "0"
    assert m.group(3) == "2"


def test_skip_strategy_basic_op():
    s = SkipStrategy.noop()
    assert not s

    s.case_comparable = Status.FAILED
    assert s.should_skip_rest_cases(Status.INCOMPLETE)
    assert s


def test_skip_strategy_round_trip():
    assert set(SkipStrategy.all_options()) == SKIP_STRATEGY_OPTIONS_ON_PAPER

    for op in SKIP_STRATEGY_OPTIONS_ON_PAPER:
        ret = SkipStrategy.from_option(op)
        assert ret.test_comparable <= Status.FAILED
        assert ret.suite_comparable <= Status.FAILED
        assert ret.case_comparable <= Status.FAILED
