import functools
import logging
import re
from unittest import mock

import pytest

from testplan.common.report import (
    BaseReportGroup,
    MergeError,
    Report,
    ReportCategories,
    RuntimeStatus,
    Status,
)
from testplan.common.report.log import LOGGER
from testplan.common.utils.testing import disable_log_propagation

DummyReport = functools.partial(Report, name="dummy")
DummyReportGroup = functools.partial(BaseReportGroup, name="dummy")


def test_report_status_basic_op():
    assert Status.ERROR <= Status.ERROR
    assert Status.FAILED > Status.ERROR
    assert Status.INCOMPLETE < Status.FAILED
    with pytest.raises(TypeError):
        Status.INCOMPLETE < Status.XPASS_STRICT
    with pytest.raises(TypeError):
        Status.XFAIL >= Status.SKIPPED
    assert Status.XFAIL != Status.XPASS
    assert Status.XFAIL is not Status.XPASS
    assert Status.UNKNOWN < Status.NONE
    assert not Status.NONE

    assert Status.XPASS_STRICT.normalised() is Status.FAILED
    assert Status.PASSED.normalised() is Status.PASSED

    assert not Status.INCOMPLETE.precede(Status.XPASS_STRICT)
    assert Status.INCOMPLETE.precede(Status.FAILED)


def test_report_status_precedent():
    """
    `precedent` should return the value with the
    highest precedence (the lowest index).
    """

    assert Status.FAILED == Status.precedent([Status.FAILED, Status.UNKNOWN])
    assert Status.ERROR == Status.precedent([Status.ERROR, Status.UNKNOWN])
    assert Status.INCOMPLETE == Status.precedent(
        [Status.INCOMPLETE, Status.UNKNOWN]
    )
    assert Status.XPASS_STRICT == Status.precedent(
        [Status.XPASS_STRICT, Status.UNKNOWN]
    )
    assert Status.UNKNOWN == Status.precedent([Status.UNKNOWN, Status.PASSED])
    assert Status.PASSED == Status.precedent([Status.PASSED, Status.SKIPPED])
    assert Status.PASSED == Status.precedent([Status.PASSED, Status.XFAIL])
    assert Status.PASSED == Status.precedent([Status.PASSED, Status.XPASS])
    assert Status.PASSED == Status.precedent([Status.PASSED, Status.UNSTABLE])
    assert Status.UNSTABLE == Status.precedent([Status.UNSTABLE, Status.NONE])


@disable_log_propagation(LOGGER)
def test_exception_logger_suppression():
    """ExceptionLoggerBase should suppress and log given exceptions."""
    rep = DummyReport()
    exc_str = None

    with rep.logged_exceptions():
        raise Exception("foo")

    original_log = rep.logs[0]

    assert original_log["levelname"] == "ERROR"
    assert original_log["levelno"] == logging.ERROR
    assert re.match(r"foo", original_log["message"])


@disable_log_propagation(LOGGER)
def test_exception_logger_reraise():
    """
    ExceptionLogger.* should raise the exception without logging
    if it doesn't match `exception_classes`.
    """
    rep = DummyReport()

    with pytest.raises(KeyError):
        with rep.logged_exceptions(IndexError):
            raise IndexError("foo")  # suppressed

        with rep.logged_exceptions(IndexError):
            raise KeyError("bar")  # raised

    rep = DummyReportGroup()

    with pytest.raises(KeyError):
        with rep.logged_exceptions(IndexError):
            raise IndexError("foo")  # suppressed

        with rep.logged_exceptions(IndexError):
            raise KeyError("bar")  # raised


class TestReport:
    def test_equality(self):
        """Should return True if core attribs match."""
        kwargs = dict(
            name="foo", description="bar", uid="uid", entries=[1, 2, 3]
        )

        rep_1 = Report(**kwargs)
        rep_2 = Report(**kwargs)

        # need to set this explicitly
        rep_2.logs = rep_1.logs

        assert rep_1 == rep_2

    @pytest.mark.parametrize(
        "override",
        (
            {"name": "bar"},
            {"description": "baz"},
            {"uid": "foo"},
            {"entries": [1, 2]},
        ),
    )
    def test_equality_fail(self, override):
        """Should return False if core attribs do not match."""
        kwargs = dict(
            name="foo", description="bar", uid="uid", entries=[1, 2, 3]
        )

        rep_1 = Report(**kwargs)
        rep_2 = Report(dict(kwargs, **override))

        # need to set this explicitly
        rep_2.logs = rep_1.logs

        assert rep_1 != rep_2

    def test_check_report_definition_name_mismatch(self):
        """Should raise ValueError on failure"""

        # These correspond to different tests
        rep_1 = DummyReport(definition_name=1)
        rep_2 = DummyReport(definition_name=2)

        with pytest.raises(AttributeError):
            rep_1._check_report(rep_2)

    def test_check_report_type_mismatch(self):
        """Should raise ValueError on failure"""

        class OtherReport(Report):
            pass

        rep_1 = DummyReport(name="foo")
        rep_2 = OtherReport(name="foo")

        with pytest.raises(TypeError):
            rep_1._check_report(rep_2)

    def test_filter(self):
        """
        Filter operation should return a copy of
        original report with filtered entries.
        """
        rep = DummyReport(
            entries=[1, 2, ["foo"], ["bar", "baz"], {"hello": "world"}]
        )

        rep_copy_1 = rep.filter(lambda val: isinstance(val, int))

        assert id(rep_copy_1) != id(rep)
        assert rep_copy_1.entries == [1, 2]

        # Filters can be chained
        rep_copy_2 = rep.filter(lambda val: not isinstance(val, int)).filter(
            lambda val: len(val) > 1, lambda val: "hello" in val
        )

        assert id(rep_copy_2) != id(rep)
        assert rep_copy_2.entries == [["bar", "baz"], {"hello": "world"}]


class DummyStatusReport:
    def __init__(self, status, uid=None):
        self.uid = uid or 0
        self.status = status


class TestBaseReportGroup:
    def test_build_index(self):
        """
        Should set `_index` attribute with child
        report `ids` as keys and child report as values.
        """
        parent = DummyReportGroup()
        children = [DummyReport(uid=idx) for idx in range(3)]

        assert parent._index == {}

        parent.entries = children
        parent.build_index()

        assert parent._index == {
            child.uid: i for i, child in enumerate(children)
        }

    def test_build_index_recursive(self):
        """Recursive index build should propagate to all children."""
        child_1, child_2, child_3, child_4 = [
            DummyReport(uid=idx) for idx in range(4)
        ]

        parent_1 = DummyReportGroup(uid=0)
        parent_2 = DummyReportGroup(uid=1)
        grand_parent = DummyReportGroup()

        assert grand_parent._index == {}
        assert parent_1._index == {}
        assert parent_2._index == {}

        parent_1.entries = [child_1, child_2]
        parent_2.entries = [child_3, child_4]
        grand_parent.entries = [parent_1, parent_2]

        grand_parent.build_index(recursive=True)

        assert grand_parent._index == {parent_1.uid: 0, parent_2.uid: 1}

        assert parent_1._index == {child_1.uid: 0, child_2.uid: 1}

        assert parent_2._index == {child_3.uid: 0, child_4.uid: 1}

    def test_build_index_dupe_child_id(self):
        """Index build should fail if children have the same IDs."""
        rep_1 = DummyReport(uid=5)
        rep_2 = DummyReport(uid=5)

        parent = DummyReportGroup()
        parent.entries = [rep_1, rep_2]

        with pytest.raises(ValueError):
            parent.build_index()

    def test_merge_logs(self):
        """
        Log merge should update `_logs` dict with
        report's `local_uid` and should be idempotent.
        """
        rep_1 = DummyReportGroup(uid=5)
        rep_2 = DummyReportGroup(uid=5)

        rep_1.logger.info("foo")
        rep_1.logger.debug("bar")

        rep_2.logger.info("baz")
        rep_2.logger.critical("bat")

        expected = rep_1.logs + rep_2.logs

        rep_1.merge(rep_2)

        assert rep_1.logs == expected

        # Log merge should be idempotent
        rep_1.merge(rep_2)
        assert rep_1.logs == expected

    def test_merge_entries(self):
        """Should merge each children separately."""
        child_clone_1 = DummyReport(uid=10)
        child_clone_2 = DummyReport(uid=20)
        parent_clone = DummyReportGroup(
            uid=1, entries=[child_clone_1, child_clone_2]
        )

        child_orig_1 = DummyReport(uid=10)
        child_orig_2 = DummyReport(uid=20)
        parent_orig = DummyReportGroup(
            uid=1, entries=[child_orig_1, child_orig_2]
        )

        with mock.patch.object(child_orig_1, "merge"):
            with mock.patch.object(child_orig_2, "merge"):
                parent_orig.merge(parent_clone, strict=True)
                child_orig_1.merge.assert_called_once_with(
                    child_clone_1, strict=True
                )
                child_orig_2.merge.assert_called_once_with(
                    child_clone_2, strict=True
                )

    def test_merge_entries_fail(self):
        """Should raise `MergeError` if child `uid`s do not match."""
        child_clone_1 = DummyReport(uid=10)
        child_clone_2 = DummyReport(uid=20)
        parent_clone = DummyReportGroup(
            uid=1, entries=[child_clone_1, child_clone_2]
        )

        child_orig_1 = DummyReport(uid=1)
        parent_orig = DummyReportGroup(uid=10, entries=[child_orig_1])

        with pytest.raises(MergeError):
            parent_orig.merge(parent_clone)

    def test_append(self):
        """`ReportGroup.append` should append the `report` to `self.entries` and update `self._index`."""
        group = DummyReportGroup()
        child = DummyReport()

        assert group.entries == []
        assert group._index == {}

        group.append(child)

        assert group.entries == [child]
        assert group._index == {child.uid: 0}

    def test_append_type_error(self):
        """`ReportGroup.append` should raise `TypeError` if `report` is not of type `Report`."""
        with pytest.raises(TypeError):
            DummyReportGroup().append(object())

    def test_append_value_error(self):
        """
        `ReportGroup.append` should raise `ValueError` if `self._index`
        has already a matching key to `report.uid`.
        """

        child = DummyReport()
        group = DummyReportGroup(entries=[child])

        with pytest.raises(ValueError):
            group.append(child)

    def test_filter(self):
        """Filter operation should be applied recursively."""

        def num_filter(obj):
            if isinstance(obj, int):
                return obj % 2 == 0
            return True

        def node_filter(obj):
            if isinstance(obj, (Report, BaseReportGroup)):
                return obj.name in ["foo", "bar", "alpha", "beta", "root"]
            return True

        child_1 = DummyReport(name="foo", entries=[1, 2, 3])
        child_2 = DummyReport(name="bar", entries=[3, 4, 5])
        child_3 = DummyReport(name="baz", entries=[4, 5, 6])

        group_1 = DummyReportGroup(name="alpha", entries=[child_1, child_2])
        group_2 = DummyReportGroup(name="beta", entries=[child_3])
        group_3 = DummyReportGroup(name="gamma", entries=[])

        root = DummyReportGroup(
            name="root", entries=[group_1, group_2, group_3]
        )

        filtered = root.filter(node_filter).filter(num_filter)

        assert filtered.name == "root"
        assert len(filtered.entries) == 2

        assert filtered.entries[0].name == "alpha"
        assert filtered.entries[0].entries[0].name == "foo"
        assert filtered.entries[0].entries[1].name == "bar"

        assert filtered.entries[0].entries[0].entries == [2]
        assert filtered.entries[0].entries[1].entries == [4]

        assert filtered.entries[1].name == "beta"
        assert (
            filtered.entries[1].entries == []
        )  # children filtered out, names don't match

    def test_parent_uids(self):
        """
        Test that the parent UIDs are correctly set of child elements. The
        child is added to the parent before the parent is added to the
        grand-parent. The child should have both grand-parent and parent UIDs.
        """
        parent = DummyReportGroup()
        child = DummyReport()
        parent.append(child)

        assert child in parent.entries
        assert child.parent_uids == [parent.uid]

        grand_parent = DummyReportGroup()
        grand_parent.append(parent)

        assert parent in grand_parent.entries
        assert parent.parent_uids == [grand_parent.uid]
        assert child.parent_uids == [grand_parent.uid, parent.uid]

    def test_parent_uids_2(self):
        """
        Test that the parent UIDs are correctly set on child elements. The
        parent is added to the grand-parent before the child is added to the
        parent. The child should have both grand-parent and parent UIDs.
        """
        grand_parent = DummyReportGroup()
        parent = DummyReportGroup()
        child = DummyReport()

        grand_parent.append(parent)
        parent.append(child)

        assert parent.parent_uids == [grand_parent.uid]
        assert child.parent_uids == [grand_parent.uid, parent.uid]

    def test_graft_round_trip(self):
        grand_parent = DummyReportGroup()
        parent = DummyReportGroup()
        child = DummyReport()

        grand_parent.append(parent)
        parent.append(child)

        refs = list(grand_parent.pre_order_iterate())
        parts = list(grand_parent.pre_order_disassemble())

        # disassembled in place
        assert not grand_parent.entries
        assert all(map(lambda x, y: x is y, refs, parts))

        child.parent_uids.clear()
        parent.parent_uids.clear()

        grand_parent.graft_entry(parent, [])
        grand_parent.graft_entry(child, [parent.uid])

        assert child.parent_uids == ["dummy", "dummy"]
        assert parent.parent_uids == ["dummy"]
        assert "dummy" in grand_parent
        assert "dummy" in parent

    @pytest.mark.parametrize(
        "statuses,expected",
        (
            ([Status.ERROR, Status.FAILED, Status.PASSED], Status.ERROR),
            ([Status.FAILED, Status.PASSED], Status.FAILED),
            (
                [Status.INCOMPLETE, Status.PASSED, Status.SKIPPED],
                Status.INCOMPLETE,
            ),
            ([Status.SKIPPED, Status.PASSED], Status.PASSED),
            ([Status.INCOMPLETE, Status.FAILED], Status.INCOMPLETE),
        ),
    )
    def test_status(self, statuses, expected):
        """Should return the precedent status from children."""

        reports = [
            DummyStatusReport(uid=idx, status=status)
            for idx, status in enumerate(statuses)
        ]
        group = DummyReportGroup(entries=reports)
        assert group.status == expected

    def test_status_no_entries(self):
        """
        Should return Status.UNKNOWN when `status_override`
        is None and report has no entries.
        """
        group = DummyReportGroup()

        assert group.status_override is Status.NONE
        assert group.status == Status.UNKNOWN

    def test_status_override(self):
        """
        `status_override` of a group should take
        precedence over child statuses.
        """
        group = DummyReportGroup(
            entries=[DummyStatusReport(status=Status.FAILED)]
        )

        assert group.status == Status.FAILED

        group.status_override = Status.PASSED

        assert group.status == Status.PASSED

    def test_merge(self):
        """
        Should merge children and set `status_override`
        using `report.status_override` precedence.
        """
        report_orig = DummyReportGroup(uid=1)
        report_clone = DummyReportGroup(uid=1)

        assert report_orig.status_override is Status.NONE

        report_clone.status_override = Status.PASSED

        with mock.patch.object(report_orig, "merge_entries"):
            report_orig.merge(report_clone)
            report_orig.merge_entries.assert_called_once_with(
                report_clone, strict=True
            )
            assert report_orig.status_override == report_clone.status_override

    def test_hash(self):
        """
        Test that a hash is generated for report groups, which depends on the
        entries they contain.
        """
        grand_parent = DummyReportGroup()
        parent = DummyReportGroup()
        child = Report(name="testcase")

        orig_root_hash = grand_parent.hash

        grand_parent.append(parent)
        updated_root_hash = grand_parent.hash
        assert updated_root_hash != orig_root_hash

        parent.append(child)

        orig_root_hash = updated_root_hash
        updated_root_hash = grand_parent.hash
        assert updated_root_hash != orig_root_hash

        child.append({"name": "entry", "passed": True})

        orig_root_hash = updated_root_hash
        updated_root_hash = grand_parent.hash
        assert updated_root_hash != orig_root_hash


def test_report_categories_type():
    assert ReportCategories.MULTITEST == "multitest"
    assert type(ReportCategories.MULTITEST) is str


def test_runtime_status_basic_op():
    assert RuntimeStatus.WAITING < RuntimeStatus.READY
    assert RuntimeStatus.RESETTING >= RuntimeStatus.RUNNING
    assert RuntimeStatus.RUNNING.precede(RuntimeStatus.FINISHED)
    assert RuntimeStatus.NOT_RUN < RuntimeStatus.NONE
    assert not RuntimeStatus.NONE

    assert RuntimeStatus.NOT_RUN.to_json_compatible() == "not_run"
    assert (
        RuntimeStatus.from_json_compatible("not_run") == RuntimeStatus.NOT_RUN
    )
