from testplan.report.testing.base import Status
from testplan.testing.common import (
    TEST_PART_PATTERN_FORMAT_STRING,
    TEST_PART_PATTERN_REGEX,
    TestBreakerThres,
)

BREAKER_OPTIONS_ON_PAPER = {
    "plan-on-error",
    "plan-on-failed",
    "test-on-error",
    "test-on-failed",
    "suite-on-error",
    "suite-on-failed",
}


def test_part_pattern():
    mt_name = TEST_PART_PATTERN_FORMAT_STRING.format("MT", 0, 2)
    m = TEST_PART_PATTERN_REGEX.match(mt_name)
    assert m.group(1) == "MT"
    assert m.group(2) == "0"
    assert m.group(3) == "2"


def test_breaker_thres_round_flight():
    assert set(TestBreakerThres.reps()) == BREAKER_OPTIONS_ON_PAPER

    for op in BREAKER_OPTIONS_ON_PAPER:
        ret = TestBreakerThres.parse(op)
        assert ret.plan_level <= Status.FAILED if ret.plan_level else True
        assert ret.test_level <= Status.FAILED if ret.test_level else True
        assert ret.suite_level <= Status.FAILED if ret.suite_level else True
