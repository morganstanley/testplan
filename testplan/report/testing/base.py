"""
Report classes that will store the test results.

Assuming we have a Testplan setup like this:

.. code-block:: python

  Testplan MyPlan
    Multitest A
      Suite A-1
        TestCase test_method_a_1_x
        TestCase test_method_a_1_y
        TestCase (parametrized, with 3 scenarios) test_method_a_1_z
      Suite A-2
        Testcase test_method_a_2_x
    Multitest B
      Suite B-1
        Testcase test_method_b_1_x
    GTest C

We will have a report tree like:

.. code-block:: python

  TestReport(name='MyPlan')
    TestGroupReport(name='A', category='Multitest')
      TestGroupReport(name='A-1', category='TestSuite')
        TestCaseReport(name='test_method_a_1_x')
        TestCaseReport(name='test_method_a_1_y')
        TestGroupReport(name='test_method_a_1_z', category='parametrization')
          TestCaseReport(name='test_method_a_1_z_1')
          TestCaseReport(name='test_method_a_1_z_2')
          TestCaseReport(name='test_method_a_1_z_3')
      TestGroupReport(name='A-2', category='TestSuite')
        TestCaseReport(name='test_method_a_2_x')
    TestGroupReport(name='B', category='MultiTest')
      TestGroupReport(name='B-1', category='TestSuite')
        TestCaseReport(name='test_method_b_1_x')
    TestGroupReport(name='C', category='GTest')
      TestCaseReport(name='<first test of Gtest>') -> can only be retrieved
                                                      after GTest is run
      TestCaseReport(name='<second test of Gtest>') -> can only be retrieved
                                                       after GTest is run
    ...
"""
import os
import copy
import collections
import inspect
import hashlib
import itertools

from marshmallow import exceptions

from testplan.common.report import (
    ExceptionLogger as ExceptionLoggerBase, Report, ReportGroup)
from testplan.common.utils import timing
from testplan.common.utils.exceptions import format_trace
from testplan.testing import tagging


class Status(object):
    """
    Report status constants and utilities for getting precedent statuses.
    """
    ERROR = 'error'
    FAILED = 'failed'
    INCOMPLETE = 'incomplete'
    PASSED = 'passed'
    SKIPPED = 'skipped'
    READY = 'ready'
    RUNNING = 'running'

    STATUS_PRECEDENCE = (
        RUNNING,
        READY,
        ERROR,
        FAILED,
        INCOMPLETE,
        PASSED,
        SKIPPED,
    )

    # `status_override` can be None, so need to add it to precedence rules
    STATUS_OVERRIDE_PRECEDENCE = STATUS_PRECEDENCE + (None,)

    @classmethod
    def precedent(cls, stats, rule=STATUS_PRECEDENCE):
        """
        Return the precedent status from a list of statuses, using the
        ordering of statuses in `rule`.

        :param stats: List of statuses of which we want to get the precedent.
        :type stats: ``sequence``
        :param rule: Precedence rules for the given statuses.
        :type rule: ``sequence``
        """
        return min(stats, key=lambda stat: rule.index(stat))


_TestCount = collections.namedtuple('_TestCount', Status.STATUS_PRECEDENCE)


class TestCount(_TestCount):

    @property
    def total(self):
        return sum(getattr(self, attrname) for attrname in self._fields)


class ExceptionLogger(ExceptionLoggerBase):
    """
    When we run tests, we always want to return a report object,
    However we also want to mark the test as failed if an
    exception is raised (unless kwargs['fail'] is `False`).
    """

    def __init__(self, *exception_classes, **kwargs):
        self.fail = kwargs.get('fail', True)
        super(ExceptionLogger, self).__init__(*exception_classes, **kwargs)

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None and issubclass(exc_type,
                                               self.exception_classes):

            # Custom exception message with extra args
            exc_msg = format_trace(inspect.trace(), exc_value)
            self.report.logger.error(exc_msg)

            if self.fail:
                self.report.status_override = Status.ERROR
            return True


class BaseReportGroup(ReportGroup):
    """Base container report for tests, relies on children's statuses."""

    exception_logger = ExceptionLogger

    def __init__(self, *args, **kwargs):
        self.meta = kwargs.pop('meta', {})
        super(BaseReportGroup, self).__init__(*args, **kwargs)
        self.status_override = None
        self.timer = timing.Timer()
        self._status = Status.READY

    def _get_comparison_attrs(self):
        return super(BaseReportGroup, self)._get_comparison_attrs() +\
            ['status_override', 'timer']

    @property
    def passed(self):
        """Shortcut for getting if report status is `Status.PASSED`."""
        return self.status == Status.PASSED

    @property
    def failed(self):
        """
        Shortcut for checking if report status is `Status.FAILED` or
        `Status.ERROR`.
        """
        return self.status in (Status.FAILED, Status.ERROR)

    @property
    def running(self):
        """
        Shortcut for checking if report status is `Status.RUNNING`.
        """
        return self.status == Status.RUNNING

    @property
    def status(self):
        """
        Status of the report, will be used to decide
        if a Testplan run has completed successfully or not.

        `status_override` always takes precedence,
        otherwise we fall back to precedent status from `self.entries`.

        If a report group has no children, it is assumed to be passing.
        """
        if self.status_override:
            return self.status_override

        if self.entries:
            return Status.precedent([entry.status for entry in self])

        return self._status

    @status.setter
    def status(self, new_status):
        for entry in self:
            entry.status = new_status
        self._status = new_status

    def merge_children(self, report, strict=True):
        """
        For report groups, we call `merge` on each child report
        and later merge basic attributes.

        However sometimes original report may not have matching child reports.
        For example this happens when the test target's test cases cannot be
        inspected on initialization time (e.g. GTest).

        In this case we can merge with `strict=False` so that child reports
        are directly appended to original report's entries.
        """
        if strict:
            super(BaseReportGroup, self).merge_children(report, strict=strict)
        else:
            for entry in report:
                if entry.uid not in self._index:
                    self.append(entry)
                else:
                    self.get_by_uid(entry.uid).merge(entry, strict=strict)

    def merge(self, report, strict=True):
        """Update `status_override` as well."""
        super(BaseReportGroup, self).merge(report, strict=strict)

        self.timer.update(report.timer)
        self.status_override = Status.precedent(
            [self.status_override, report.status_override],
            rule=Status.STATUS_OVERRIDE_PRECEDENCE)

    @property
    def counts(self):
        """
        Return counts for each status, will recursively get aggregates from
        children and so on.
        """

        def _get_counts(obj, status):
            count = 0
            for child in obj:
                if isinstance(child, TestCaseReport) and child.status == status:
                    count += 1
                elif isinstance(child, BaseReportGroup):
                    count += _get_counts(child, status)
            return count

        return TestCount(*[_get_counts(self, stat)
                           for stat in Status.STATUS_PRECEDENCE])

    def filter(self, *functions, **kwargs):
        """
        Tag indices are updated after filter operations.
        """
        result = super(BaseReportGroup, self).filter(*functions, **kwargs)

        # We'd like to call tag propagation before returning the root node,
        # so we rely on absence of implicit `__copy` arg to decide if we should
        # trigger tag index propagation or not. If we don't do this check
        # then tag propagation will be called for each filter call on
        # sub-nodes which is going to be a redundant operation.

        if kwargs.get('__copy', True):
            result.propagate_tag_indices()
        return result

    def filter_by_tags(self, tag_value, all_tags=False):
        """Shortcut method for filtering the report by given tags."""
        def _filter_func(obj):
            # Include all testcase entries, which are in dict form
            if isinstance(obj, dict):
                return True

            tag_dict = tagging.validate_tag_value(tag_value)
            if all_tags:
                match_func = tagging.check_all_matching_tags
            else:
                match_func = tagging.check_any_matching_tags

            return match_func(
                tag_arg_dict=tag_dict, target_tag_dict=obj.tags_index)

        return self.filter(_filter_func)


class TestReport(BaseReportGroup):
    """
    Report for a Testplan test run, sits at the root of the report tree.
    Only contains TestGroupReports as children.
    """

    def __init__(self, meta=None, attachments=None, *args, **kwargs):
        self.meta = meta or {}
        self._tags_index = None

        # Report attachments: Dict[dst: str, src: str].
        # Maps from destination path (relative from attachments root dir)
        # to the full source path (absolute or relative from cwd).
        self.attachments = attachments or {}

        super(TestReport, self).__init__(*args, **kwargs)

    @property
    def tags_index(self):
        """
        Root report only has tag indexes, which is only useful when
        we run searches against multiple test reports.
        (e.g Give me all test runs from all projects that have these tags)
        """
        from testplan.testing.tagging import merge_tag_dicts
        if self._tags_index is None:
            self._tags_index = merge_tag_dicts(
                *[child.tags_index for child in self])
        return self._tags_index

    def propagate_tag_indices(self):
        """
        TestReport does not have native tag data,
        so it just triggers children's tag updates.
        """
        for child in self:
            child.propagate_tag_indices()

        # reset tags index, so it gets repopulated on the next call
        self._tags_index = None

    def bubble_up_attachments(self):
        """
        Attachments are saved at various levels of the report:

          * Fix spec file attached to multitests.
          * When implemented result.attach will attach files to assertions.

        This iterates through the report entries and bubbles up all the
        attachments to the top level. This top level dictionary of attachments
        will be used by Exporters to export attachments as well as the report.
        """
        for child in self:
            if getattr(child, 'fix_spec_path', None):
                self._bubble_up_fix_spec(child)
            for attachment in child.attachments:
                self.attachments[attachment.dst_path] = attachment.source_path

    def _bubble_up_fix_spec(self, child):
        """Bubble up a "fix_spec_path" from a child report."""
        real_path = child.fix_spec_path
        hash_dir = hashlib.md5(real_path.encode('utf-8')).hexdigest()
        hash_path = os.path.join(
            hash_dir,
            os.path.basename(child.fix_spec_path)
        )
        child.fix_spec_path = hash_path
        self.attachments[hash_path] = real_path

    def _get_comparison_attrs(self):
        return super(TestReport, self)._get_comparison_attrs() +\
            ['tags_index', 'meta']

    def serialize(self):
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestReportSchema
        return TestReportSchema(strict=True).dump(self).data

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestReport`` object (and its children)
        from nested python dictionaries.
        """
        from .schemas import TestReportSchema
        return TestReportSchema(strict=True).load(data).data

    def shallow_serialize(self):
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestReportSchema
        return ShallowTestReportSchema(strict=True).dump(self).data

    @classmethod
    def shallow_deserialize(cls, data, old_report):
        """
        Shortcut for deserializing a ``TestReport`` object from its shallow
        serialized representation.
        """
        from .schemas import ShallowTestReportSchema
        deserialized = ShallowTestReportSchema(strict=True).load(data).data
        deserialized.entries = old_report.entries
        deserialized._index = old_report._index

        return deserialized


class TestGroupReport(BaseReportGroup):
    """
    A middle-level container report, can contain both TestGroupReports and
    TestCaseReports.
    """

    def __init__(
        self, name, description=None,
        category=None, uid=None, entries=None,
        tags=None, part=None, fix_spec_path=None
    ):
        super(TestGroupReport, self).__init__(
            name=name, description=description, uid=uid, entries=entries)

        # This will be used for distinguishing test
        # type (Multitest, GTest etc)
        self.category = category

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)

        # A test can be split into many parts and the report of each part
        # can be hold back for merging (if necessary)
        self.part = part  # i.e. (m, n), while 0 <= m < n and n > 1
        self.part_report_lookup = {}

        self.fix_spec_path = fix_spec_path

        if entries:
            self.propagate_tag_indices()

    def __str__(self):
        return (
            '{kls}(name="{name}", category="{category}", id="{uid}"),'
            ' tags={tags})'
        ).format(
            kls=self.__class__.__name__,
            name=self.name,
            category=self.category,
            uid=self.uid,
            tags=self.tags or None,
        )

    def __repr__(self):
        return (
            '{kls}(name="{name}", category="{category}", id="{uid}",'
            ' entries={entries}, tags={tags})'
        ).format(
            kls=self.__class__.__name__,
            name=self.name,
            category=self.category,
            uid=self.uid,
            entries=repr(self.entries),
            tags=self.tags or None,
        )

    def _get_comparison_attrs(self):
        return super(TestGroupReport, self)._get_comparison_attrs() +\
            ['category', 'tags', 'tags_index']

    def append(self, item):
        """Update tag indices if item or self has tag data."""
        super(TestGroupReport, self).append(item)
        if self.tags_index or item.tags_index:
            self.propagate_tag_indices()

    def serialize(self, strict=True):
        """
        Shortcut for serializing TestGroupReport data to nested python
        dictionaries.
        """
        from .schemas import TestGroupReportSchema
        return TestGroupReportSchema(strict=strict).dump(self).data

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestGroupReport`` object
        (and its children) from nested python dictionaries.
        """
        from .schemas import TestGroupReportSchema
        return TestGroupReportSchema(strict=True).load(data).data

    def shallow_serialize(self):
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestGroupReportSchema
        return ShallowTestGroupReportSchema(strict=True).dump(self).data

    @classmethod
    def shallow_deserialize(cls, data, old_report):
        """
        Shortcut for deserializing a ``TestGroupReport`` object from its
        shallow serialized representation.
        """
        from .schemas import ShallowTestGroupReportSchema
        deserialized = ShallowTestGroupReportSchema(
            strict=True).load(data).data
        deserialized.entries = old_report.entries
        deserialized._index = old_report._index
        return deserialized

    def _collect_tag_indices(self):
        """
        Recursively collect tag indices from children (and their children etc)
        """
        tag_dicts = [self.tags]

        for child in self:
            if isinstance(child, TestGroupReport):
                tag_dicts.append(child._collect_tag_indices())
            elif isinstance(child, TestCaseReport):
                tag_dicts.append(child.tags)
        return tagging.merge_tag_dicts(*tag_dicts)

    def propagate_tag_indices(self, parent_tags=None):
        """
        Distribute native tag data onto `tags_index` attributes on the nodes
        of the test report. This distribution happens 2 ways.
        """
        tags_index = tagging.merge_tag_dicts(self.tags, parent_tags or {})

        for child in self:
            if isinstance(child, TestGroupReport):
                child.propagate_tag_indices(parent_tags=tags_index)

            elif isinstance(child, TestCaseReport):
                child.tags_index = tagging.merge_tag_dicts(
                    child.tags, tags_index)

        self.tags_index = tagging.merge_tag_dicts(
            tags_index, self._collect_tag_indices())

    def merge(self, report, strict=True):
        """Propagate tag indices after merge operations."""
        super(TestGroupReport, self).merge(report, strict=strict)
        self.propagate_tag_indices()

    @property
    def attachments(self):
        """Return all attachments from child reports."""
        return itertools.chain.from_iterable(
            child.attachments for child in self)


class TestCaseReport(Report):
    """
    Leaf of the report tree, contains serialized assertion / log entries.
    """

    exception_logger = ExceptionLogger

    def __init__(self,
                 name,
                 description=None,
                 uid=None,
                 entries=None,
                 tags=None,
                 suite_related=False):
        super(TestCaseReport, self).__init__(
            name=name, uid=uid, entries=entries, description=description)

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)
        self.suite_related = suite_related

        self.status_override = None
        self.timer = timing.Timer()

        self.attachments = []
        self._status = Status.READY

    def _get_comparison_attrs(self):
        return super(TestCaseReport, self)._get_comparison_attrs() +\
            ['status_override', 'timer', 'tags', 'tags_index']

    @property
    def passed(self):
        """Shortcut for getting if report status is `Status.PASSED`."""
        return self.status == Status.PASSED

    @property
    def failed(self):
        """
        Shortcut for checking if report status is `Status.FAILED` or
        `Status.ERROR`.
        """
        return self.status in (Status.FAILED, Status.ERROR)

    @property
    def running(self):
        """
        Shortcut for checking if report status is `Status.RUNNING`.
        """
        return self.status == Status.RUNNING

    @property
    def status(self):
        """
        Entries in this context correspond to serialized (raw)
        assertions / custom logs in dictionary form.
        Assertion dicts will have a `passed` key
        which will be set to `False` for failed assertions.
        """
        if self.status_override:
            return self.status_override

        if self.entries:
            return self._assertions_status()
        return self._status

    @status.setter
    def status(self, new_status):
        """
        Update the status of a testcase. This status is only used for a
        testcase containing no entries, otherwise the status of the entries
        is used with precedence rules.

        As a special case, when setting the status of a testcase to "running",
        any entries from a previous run are discarded, so the status is
        guaranteed to be read as "running".
        """
        self._status = new_status
        if new_status == "running":
            self.entries = []

    def _assertions_status(self):
        for entry in self:
            if entry.get("passed") is False:
                return Status.FAILED
        return Status.PASSED

    def merge(self, report, strict=True):
        """
        TestCaseReport merge overwrites everything in place, as assertions of
        a test case won't be split among different runners. For some special
        test cases, choose the one whose status is of higher precedence.
        """
        self._check_report(report)
        if self.suite_related and \
                Status.precedent([self.status]) < \
                Status.precedent([report.status]):
            return

        self.status_override = report.status_override
        self.logs = report.logs
        self.entries = report.entries
        self.timer = report.timer

    def flattened_entries(self, depth):
        """Need to take assertion groups into account."""
        def flatten_dicts(dicts, _depth):
            """Recursively flatten serialized entry list."""
            result = []
            for d in dicts:
                result.append((_depth, d))
                if d['type'] == 'Group' or d['type'] == 'Summary':
                    result.extend(flatten_dicts(d['entries'], _depth + 1))
            return result
        return flatten_dicts(self.entries, depth)

    def serialize(self):
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema
        return TestCaseReportSchema(strict=True).dump(self).data

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestCaseReport`` object
        from nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema
        return TestCaseReportSchema(strict=True).load(data).data

