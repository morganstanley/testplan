import functools
import gc
import weakref

from testplan.common.report import BaseReportGroup, Report, Status
from testplan.common.report.cache import report_cache
from testplan.report import TestCaseReport, TestGroupReport
from testplan.report.testing.schemas import TestGroupReportSchema

DummyGroup = functools.partial(BaseReportGroup, name="dummy")


def make_case(name, passed=True):
    case = TestCaseReport(name=name)
    case.entries.append({"uid": "a", "type": "Equal", "passed": passed})
    return case


def test_cache_off_by_default():
    case = make_case("case")
    assert case.status == Status.PASSED
    case.entries[0]["passed"] = False
    # No block, so the next read sees the change
    assert case.status == Status.FAILED


def test_cache_holds_inside_block():
    case = make_case("case")
    with report_cache():
        assert case.status == Status.PASSED
        case.entries[0]["passed"] = False
        assert case.status == Status.PASSED
    # The value does not outlive the block
    assert case.status == Status.FAILED


def test_setter_still_works():
    group = DummyGroup()
    group.append(Report(name="child"))
    with report_cache():
        group.status_override = Status.UNSTABLE
        assert group.status == Status.UNSTABLE
    group.status_override = Status.NONE

    # A childless group falls back to the value the setter wrote
    empty = DummyGroup()
    empty.status = Status.ERROR
    assert empty.status == Status.ERROR


def test_dump_matches_uncached():
    group = TestGroupReport(name="group", category="testsuite")
    group.append(make_case("ok"))
    group.append(make_case("bad", passed=False))

    plain = TestGroupReportSchema().dump(group)
    with report_cache():
        cached = TestGroupReportSchema().dump(group)
    assert cached == plain


def test_cache_keeps_node_alive():
    case = make_case("case")
    ref = weakref.ref(case)
    with report_cache():
        case.status
        del case
        gc.collect()
        assert ref() is not None
    gc.collect()
    assert ref() is None
