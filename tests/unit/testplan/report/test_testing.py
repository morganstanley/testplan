import functools

import pytest
import mock

from testplan.common.utils.testing import disable_log_propagation

from testplan.report.testing.base import (
    Status,
    BaseReportGroup,
    TestCaseReport,
    TestGroupReport,
    TestReport,
    ReportCategories,
)
from testplan.report.testing.schemas import TestReportSchema
from testplan.common import report
from testplan.common.utils.testing import check_report


DummyReport = functools.partial(report.Report, name='dummy')
DummyReportGroup = functools.partial(BaseReportGroup, name='dummy')


def test_report_status_precedent():
    """
    `precedent` should return the value with the
    highest precedence (the lowest index).
    """

    assert Status.PASSED == Status.precedent([Status.PASSED, Status.XPASS])
    assert Status.FAILED == Status.precedent([Status.PASSED, Status.FAILED])
    assert Status.READY == Status.precedent([Status.READY, Status.PASSED])
    assert Status.FAILED == Status.precedent([Status.FAILED])
    assert Status.PASSED == Status.precedent([Status.PASSED, Status.XFAIL])
    assert Status.FAILED == Status.precedent([Status.FAILED, Status.XFAIL])


@disable_log_propagation(report.log.LOGGER)
def test_report_exception_logger():
    """
      `TestReportExceptionLogger` should set `status_override` to
      `TestReportStatus.FAILED` if `fail` argument is True.
    """
    rep = TestCaseReport(name='foo')
    assert rep.status_override is None

    # should not change status_override
    with rep.logged_exceptions(fail=False):
        raise Exception('foo')

    assert rep.status_override is None

    # should change status_override
    with rep.logged_exceptions():
        raise Exception('foo')

    assert rep.status_override is Status.ERROR


class DummyStatusReport(object):

    def __init__(self, status, uid=None):
        self.uid = uid or 0
        self.status = status


class TestBaseReportGroup(object):

    @pytest.mark.parametrize(
        'statuses,expected',
        (
            ([Status.ERROR, Status.FAILED, Status.PASSED], Status.ERROR),
            ([Status.FAILED, Status.PASSED], Status.FAILED),
            (
                [Status.INCOMPLETE, Status.PASSED, Status.SKIPPED],
                Status.INCOMPLETE
            ),
            ([Status.SKIPPED, Status.PASSED], Status.PASSED),
            ([Status.INCOMPLETE, Status.FAILED], Status.FAILED),
        )
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
        Should return Status.READY when `status_override`
        is None and report has no entries.
        """
        group = DummyReportGroup()

        assert group.status_override is None
        assert group.status == Status.READY

    def test_status_override(self):
        """
        `status_override` of a group should take
        precedence over child statuses.
        """
        group = DummyReportGroup(
            entries=[DummyStatusReport(status=Status.FAILED)])

        assert group.status == Status.FAILED

        group.status_override = Status.PASSED

        assert group.status == Status.PASSED

    def test_merge(self):
        """
        Should merge children and set `status_override`
        using `report.status_override` precedence.
        """
        report_orig = DummyReportGroup(uid=0)
        report_clone = DummyReportGroup(uid=0)

        assert report_orig.status_override is None

        report_clone.status_override = Status.PASSED

        with mock.patch.object(report_orig, 'merge_children'):
            report_orig.merge(report_clone)
            report_orig.merge_children.assert_called_once_with(
                report_clone, strict=True)
            assert report_orig.status_override == report_clone.status_override

    def test_merge_children_not_strict(self):
        """
          Not strict merge should append child entries and update
          the index if they do not exist in the parent.
        """
        child_clone_1 = DummyReport(uid=1)
        child_clone_2 = DummyReport(uid=2)
        parent_clone = DummyReportGroup(
            uid=0, entries=[child_clone_1, child_clone_2])

        child_orig_1 = DummyReport(uid=1)
        parent_orig = DummyReportGroup(uid=0, entries=[child_orig_1])

        parent_orig.merge(parent_clone, strict=False)

        assert parent_orig.entries == [child_orig_1, child_clone_2]

        # Merging a second time should give us the same results
        parent_orig.merge(parent_clone, strict=False)
        assert parent_orig.entries == [child_orig_1, child_clone_2]

    def test_hash(self):
        """
        Test that a hash is generated for report groups, which depends on the
        entries they contain.
        """
        grand_parent = DummyReportGroup()
        parent = DummyReportGroup()
        child = TestCaseReport(name="testcase")

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

    def test_hash_merge(self):
        """
        Test that the hash is updated after new report entries are merged in.
        """
        parent = DummyReportGroup()
        child = TestCaseReport(name="testcase")
        parent.append(child)
        orig_parent_hash = parent.hash

        parent2 = DummyReportGroup(uid=parent.uid)
        child2 = TestCaseReport(name="testcase", uid=child.uid)
        child2.append({"name": "entry", "passed": True})
        parent2.append(child2)

        parent.merge(parent2)
        assert parent.hash != orig_parent_hash


class TestTestCaseReport(object):

    @pytest.mark.parametrize(
        'entries,expected_status',
        (
            ([], Status.READY),
            ([{'foo': 2}, {'bar': 3}], Status.PASSED),
            ([{'foo': True}], Status.PASSED),
            ([{'passed': True}], Status.PASSED),
            ([{'passed': False}], Status.FAILED),
            ([{'passed': None}], Status.PASSED),
            ([{'passed': False}, {'passed': True}], Status.FAILED)
        )
    )
    def test_status(self, entries, expected_status):
        """
          TestCaseReport status should be `Status.FAILED` if it has a
          `dict` entry with the key `passed` = `False`.
        """
        rep = TestCaseReport(name='foo', entries=entries)
        assert rep.status == expected_status

    @pytest.mark.parametrize(
        'entries,status_override',
        (
            ([], Status.PASSED),
            ([], Status.FAILED),
            ([{'passed': True}], Status.FAILED),
            ([{'passed': False}], Status.PASSED)
        )
    )
    def test_status_override(self, entries, status_override):
        """
        TestCaseReport `status_override` should
        take precedence over `status` logic.
        """
        rep = TestCaseReport(name='foo', entries=entries)
        rep.status_override = status_override
        assert rep.status == status_override

    def test_merge(self):
        """
          `TestCaseReport.merge` should assign basic attributes
          (`status_override`, `logs`, `entries`) in place.
        """
        rep = TestCaseReport(uid=1, name='foo', entries=[1, 2, 3])
        rep.logs = [4, 5, 6]
        rep.status_override = Status.PASSED

        rep2 = TestCaseReport(uid=1, name='foo', entries=[10, 20, 30])
        rep2.logs = [40, 50, 60]
        rep2.status_override = Status.FAILED

        rep.merge(rep2)

        assert rep.status_override == rep2.status_override
        assert rep.logs == rep2.logs
        assert rep.entries == rep2.entries

    def test_hash(self):
        """Test that a consistent hash can be generated for a report object."""
        rep_1 = TestCaseReport(name="testcase1")
        rep_2 = TestCaseReport(name="testcase2")

        for rep in rep_1, rep_2:
            assert rep.hash == rep.hash

        assert rep_1.hash != rep_2.hash


@disable_log_propagation(report.log.LOGGER)
@pytest.fixture
def dummy_test_plan_report():

    tag_data_1 = {'tagname': {'tag1', 'tag2'}}
    tag_data_2 = {'other_tagname': {'tag4', 'tag5'}}

    tc_1 = TestCaseReport(
        name='test_case_1',
        description='test case 1 description',
        tags=tag_data_1,
    )

    with tc_1.logged_exceptions():
        raise Exception('some error')

    tc_2 = TestCaseReport(
        name='test_case_2',
        description='test case 2 description',
        tags={},
    )

    tg_1 = TestGroupReport(
        name='Test Group 1',
        description='Test Group 1 description',
        category=ReportCategories.TESTGROUP,
        entries=[tc_1, tc_2],
        tags=tag_data_2,
    )

    tc_3 = TestCaseReport(
        name='test_case_3',
        description='test case 3 description',
        tags=tag_data_2,
    )

    tc_3.status_override = Status.PASSED

    tg_2 = TestGroupReport(
        name='Test Group 2',
        description='Test Group 2 description',
        category=ReportCategories.TESTGROUP,
        entries=[tg_1, tc_3],
        tags={},
    )

    rep = TestReport(
        name='My Plan',
        entries=[tg_2],
        meta={'foo': 'baz'}
    )

    with rep.timer.record('foo'):
        pass

    return rep


def test_report_serialization(dummy_test_plan_report):
    """Serialized & deserialized reports should be equal."""
    data = dummy_test_plan_report.serialize()
    deserialized_report = TestReport.deserialize(data)
    check_report(actual=deserialized_report, expected=dummy_test_plan_report)


def test_report_json_serialization(dummy_test_plan_report):
    """JSON Serialized & deserialized reports should be equal."""
    test_plan_schema = TestReportSchema(strict=True)
    data = test_plan_schema.dumps(dummy_test_plan_report).data
    deserialized_report = test_plan_schema.loads(data).data
    check_report(actual=deserialized_report, expected=dummy_test_plan_report)


class TestReportTags(object):

    def get_reports(self):
        tc_report_1 = TestCaseReport(
            name='My Test Case',
            tags={'simple': {'baz'}},
        )

        tc_report_2 = TestCaseReport(
            name='My Test Case 2',
            tags={'simple': {'bat'}},
        )

        tg_report_3 = TestGroupReport(
            name='My Group 3',
            category=ReportCategories.TESTGROUP,
            tags={},
        )

        tg_report_2 = TestGroupReport(
            name='My Group 2',
            category=ReportCategories.TESTGROUP,
            tags={'simple': {'bar'}},
            entries=[tc_report_1, tc_report_2]
        )

        tg_report_1 = TestGroupReport(
            name='My Group',
            category=ReportCategories.TESTGROUP,
            tags={'simple': {'foo'}},
            entries=[tg_report_2, tg_report_3]
        )

        return tg_report_1, tg_report_2, tg_report_3, tc_report_1, tc_report_2

    def test_tag_propagation_on_init(self):
        """
        Tag propagation should update tag indices
        of the children/parents recursively.
        """
        tg_rep_1, tg_rep_2, tg_rep_3, tc_rep_1, tc_rep_2 = self.get_reports()

        assert tg_rep_1.tags_index == {'simple': {'foo', 'bar', 'baz', 'bat'}}
        assert tg_rep_1.tags == {'simple': {'foo'}}

        assert tg_rep_2.tags_index == {'simple': {'foo', 'bar', 'baz', 'bat'}}
        assert tg_rep_2.tags == {'simple': {'bar'}}

        assert tg_rep_3.tags_index == {'simple': {'foo'}}
        assert tg_rep_3.tags == {}

        assert tc_rep_1.tags_index == {'simple': {'foo', 'bar', 'baz'}}
        assert tc_rep_1.tags == {'simple': {'baz'}}

        assert tc_rep_2.tags_index == {'simple': {'foo', 'bar', 'bat'}}
        assert tc_rep_2.tags == {'simple': {'bat'}}

    def test_tag_propagation_on_append(self):
        """
        After append operation, tag propagation should
        be triggered from the target node.
        """
        tg_rep_1, tg_rep_2, tg_rep_3, tc_rep_1, tc_rep_2 = self.get_reports()

        tc_report_3 = TestCaseReport(
            name='My Test Case 3',
            tags={'color': {'blue'}}
        )

        # root node
        tg_rep_1.append(tc_report_3)

        assert tg_rep_1.tags_index == {
            'simple': {'foo', 'bar', 'baz', 'bat'},
            'color': {'blue'}
        }

        assert tc_report_3.tags_index == {
            'simple': {'foo'},
            'color': {'blue'}
        }

    def test_tag_propagation_on_filter(self):
        """
        Tag indices should be updated after filter operations
        (starting with the original node that is getting filtered).
        """

        def filter_func(obj):
            """
            Keep all test groups, discard testcase
            report with name `My Test Case 2`
            """
            return isinstance(obj, TestGroupReport)\
                or (isinstance(obj, TestCaseReport) and
                    obj.name != 'My Test Case 2')

        tg_rep_1, tg_rep_2, tg_rep_3, tc_rep_1, tc_rep_2 = self.get_reports()

        new_tg_rep_1 = tg_rep_1.filter(filter_func)

        new_tg_rep_2, new_tg_rep_3 = new_tg_rep_1
        new_tc_rep_1 = new_tg_rep_2.entries[0]

        assert new_tc_rep_1.name == 'My Test Case'

        assert new_tg_rep_1.tags_index == {'simple': {'foo', 'bar', 'baz'}}
        assert new_tg_rep_2.tags_index == {'simple': {'foo', 'bar', 'baz'}}
        assert new_tg_rep_3.tags_index == {'simple': {'foo'}}

        # tag indices from the original should have stayed same
        assert tg_rep_1.tags_index == {'simple': {'foo', 'bar', 'baz', 'bat'}}
        assert tg_rep_2.tags_index == {'simple': {'foo', 'bar', 'baz', 'bat'}}
        assert tg_rep_3.tags_index == {'simple': {'foo'}}
        assert tc_rep_1.tags_index == {'simple': {'foo', 'bar', 'baz'}}
        assert tc_rep_2.tags_index == {'simple': {'foo', 'bar', 'bat'}}
