import logging
import functools
import re

import pytest
import mock

from testplan.common import report
from testplan.common.report.log import LOGGER

from testplan.common.utils.testing import disable_log_propagation

DummyReport = functools.partial(report.Report, name="dummy")
DummyReportGroup = functools.partial(report.ReportGroup, name="dummy")


@disable_log_propagation(LOGGER)
def test_exception_logger_suppression():
    """ExceptionLogger should suppress and log given exceptions."""
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
      ExceptionLogger should raise the exception without logging
      if it doesn't match `exception_classes`.
    """
    rep = DummyReport()

    with pytest.raises(KeyError):

        with rep.logged_exceptions(IndexError):
            raise IndexError("foo")  # suppressed

        with rep.logged_exceptions(IndexError):
            raise KeyError("bar")  # raised


class TestReport(object):
    def test_equality(self):
        """Should return True if core attribs match."""
        kwargs = dict(
            name="foo", description="bar", uid="uid", entries=[1, 2, 3]
        )

        rep_1 = report.Report(**kwargs)
        rep_2 = report.Report(**kwargs)

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

        rep_1 = report.Report(**kwargs)
        rep_2 = report.Report(dict(kwargs, **override))

        # need to set this explicitly
        rep_2.logs = rep_1.logs

        assert rep_1 != rep_2

    def test_check_report_id_mismatch(self):
        """Should raise ValueError on failure"""

        # These will have different ids
        rep_1 = DummyReport()
        rep_2 = DummyReport()

        with pytest.raises(AttributeError):
            rep_1._check_report(rep_2)

    def test_check_report_type_mismatch(self):
        """Should raise ValueError on failure"""

        class OtherReport(report.Report):
            pass

        rep_1 = DummyReport(uid=5)
        rep_2 = OtherReport(name="foo", uid=5)

        with pytest.raises(TypeError):
            rep_1._check_report(rep_2)

    def test_merge_logs(self):
        """
        Log merge should update `_logs` dict with
        report's `local_uid` and should be idempotent.
        """
        rep_1 = DummyReport(uid=5)
        rep_2 = DummyReport(uid=5)

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


class TestReportGroup(object):
    def test_build_index(self):
        """
        Should set `_index` attribute with child
        report `ids` as keys and child report as values.
        """
        parent = DummyReportGroup()
        children = [DummyReport() for idx in range(3)]

        assert parent._index == {}

        parent.entries = children
        parent.build_index()

        assert parent._index == {
            child.uid: i for i, child in enumerate(children)
        }

    def test_build_index_recursive(self):
        """Recursive index build should propagate to all children."""
        child_1, child_2, child_3, child_4 = [
            DummyReport() for idx in range(4)
        ]

        parent_1 = DummyReportGroup()
        parent_2 = DummyReportGroup()
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

    def test_merge_children(self):
        """Should merge each children separately."""
        child_clone_1 = DummyReport(uid=1)
        child_clone_2 = DummyReport(uid=2)
        parent_clone = DummyReportGroup(
            uid=0, entries=[child_clone_1, child_clone_2]
        )

        child_orig_1 = DummyReport(uid=1)
        child_orig_2 = DummyReport(uid=2)
        parent_orig = DummyReportGroup(
            uid=0, entries=[child_orig_1, child_orig_2]
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

    def test_merge_children_fail(self):
        """Should raise `MergeError` if child `uid`s do not match."""
        child_clone_1 = DummyReport(uid=1)
        child_clone_2 = DummyReport(uid=2)
        parent_clone = DummyReportGroup(
            uid=0, entries=[child_clone_1, child_clone_2]
        )

        child_orig_1 = DummyReport(uid=1)
        parent_orig = DummyReportGroup(uid=0, entries=[child_orig_1])

        with pytest.raises(report.MergeError):
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
        """`ReportGroup.append` should raise `TypeError` if `report` is not of type `report.Report`."""
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
            if isinstance(obj, (report.Report, report.ReportGroup)):
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
