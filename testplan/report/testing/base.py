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
import copy
import getpass
import hashlib
import itertools
import os
import platform
import sys
import traceback
from collections import Counter
from typing import Callable, Optional, Dict

from typing_extensions import Self

from testplan.common.report import ExceptionLogger as ExceptionLoggerBase
from testplan.common.report import Report, ReportGroup, SkipTestcaseException
from testplan.common.utils import timing
from testplan.testing import tagging


class RuntimeStatus:
    """
    Constants for test runtime status - for interactive mode
    """

    READY = "ready"
    WAITING = "waiting"
    RUNNING = "running"
    RESETTING = "resetting"
    FINISHED = "finished"
    NOT_RUN = "not_run"

    STATUS_PRECEDENCE = (
        RUNNING,
        RESETTING,
        WAITING,
        READY,
        NOT_RUN,
        FINISHED,
        None,
    )

    @classmethod
    def precedent(cls, stats, rule=STATUS_PRECEDENCE):
        """
        Return the precedent status from a list of statuses, using the
        ordering of statuses in `rule`.

        Note that the client can send RESETTING signal to reset the test report
        to its initial status, but client will not receive a temporary report
        containing RESETTING status, instead WAITING status is used and after
        reset the report goes to READY status.

        :param stats: List of statuses of which we want to get the precedent.
        :type stats: ``sequence``
        :param rule: Precedence rules for the given statuses.
        :type rule: ``sequence``
        """
        return min(stats, key=lambda stat: rule.index(stat))


class Status:
    """
    Constants for test result and utilities for propagating status upward.
    """

    ERROR = "error"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    PASSED = "passed"
    SKIPPED = "skipped"
    XFAIL = "xfail"
    XPASS = "xpass"
    XPASS_STRICT = "xpass-strict"
    UNSTABLE = "unstable"
    UNKNOWN = "unknown"

    # We only maintain precedence among these status categories
    STATUS_PRECEDENCE = (
        ERROR,  # red
        FAILED,  # red
        UNKNOWN,  # black
        PASSED,  # green
        UNSTABLE,  # yellow
        None,  # `status_override` is default to None
    )

    # And we map status to a category when we propagate upward or decide
    # if an entry should be considered error/passed/failed/unstable/unknown
    STATUS_CATEGORY = {
        ERROR: ERROR,
        FAILED: FAILED,
        INCOMPLETE: FAILED,
        XPASS_STRICT: FAILED,
        UNKNOWN: UNKNOWN,
        PASSED: PASSED,
        SKIPPED: UNSTABLE,
        XFAIL: UNSTABLE,
        XPASS: UNSTABLE,
        UNSTABLE: UNSTABLE,
        None: None,  # `status_override` is default to None
    }

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
        return min(
            [cls.STATUS_CATEGORY[stat] for stat in stats],
            key=lambda stat: rule.index(stat),
        )


class ReportCategories:
    """
    Enumeration of possible categories of report nodes.

    Note: we don't use the enum.Enum base class to simplify report
    serialization via marshmallow.
    """

    TESTPLAN = "testplan"
    TESTGROUP = "testgroup"  # test group of unspecific type?
    MULTITEST = "multitest"
    TASK_RERUN = "task_rerun"
    TESTSUITE = "testsuite"
    TESTCASE = "testcase"
    PARAMETRIZATION = "parametrization"
    GTEST = "gtest"
    GTEST_SUITE = "gtest-suite"
    CPPUNIT = "cppunit"
    CPPUNIT_SUITE = "cppunit-suite"
    BOOST_TEST = "boost-test"
    BOOST_SUITE = "boost-suite"
    HOBBESTEST = "hobbestest"
    HOBBESTEST_SUITE = "hobbestest-suite"
    PYTEST = "pytest"
    PYUNIT = "pyunit"
    UNITTEST = "unittest"
    QUNIT = "qunit"
    JUNIT = "junit"
    ERROR = "error"


class ExceptionLogger(ExceptionLoggerBase):
    """
    When we run tests, we always want to return a report object,
    However we also want to mark the test as failed if an
    exception is raised (unless kwargs['fail'] is `False`).
    """

    def __init__(self, *exception_classes, **kwargs):
        self.fail = kwargs.get("fail", True)
        super(ExceptionLogger, self).__init__(*exception_classes, **kwargs)

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            if exc_type is SkipTestcaseException:
                self.report.logger.critical(
                    'Skipping testcase "%s", reason: %s',
                    self.report.name,
                    str(exc_value),
                )
                self.report.status_override = Status.SKIPPED
            elif issubclass(exc_type, self.exception_classes):
                # Custom exception message with extra args
                exc_msg = "".join(
                    traceback.format_exception(exc_type, exc_value, tb)
                )
                self.report.logger.error(exc_msg)

                if self.fail:
                    self.report.status_override = Status.ERROR
            return True


class BaseReportGroup(ReportGroup):
    """Base container report for tests, relies on children's statuses."""

    exception_logger = ExceptionLogger

    def __init__(self, name, **kwargs):
        self.meta = kwargs.pop("meta", {})
        self.status_override = kwargs.pop("status_override", None)
        self.status_reason = kwargs.pop("status_reason", None)

        super(BaseReportGroup, self).__init__(name=name, **kwargs)

        self.timer = timing.Timer()

        # Normally, a report group inherits its statuses from its child
        # entries. However, in case there are no child entries we use the
        # following values as a fallback.
        self._status = Status.UNKNOWN
        self._runtime_status = RuntimeStatus.READY

    def _get_comparison_attrs(self):
        return super(BaseReportGroup, self)._get_comparison_attrs() + [
            "status_override",
            "timer",
        ]

    @property
    def passed(self):
        """Shortcut for getting if report status should be considered passed."""
        return Status.STATUS_CATEGORY[self.status] == Status.PASSED

    @property
    def failed(self):
        """
        Shortcut for checking if report status should be considered failed.
        """
        return Status.STATUS_CATEGORY[self.status] in (
            Status.FAILED,
            Status.ERROR,
        )

    @property
    def unstable(self):
        """
        Shortcut for checking if report status should be considered unstable.
        """
        return Status.STATUS_CATEGORY[self.status] == Status.UNSTABLE

    @property
    def unknown(self):
        """
        Shortcut for checking if report status is unknown.
        """
        return Status.STATUS_CATEGORY[self.status] == Status.UNKNOWN

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
        self._status = new_status

    @property
    def runtime_status(self):
        """
        The runtime status is used for interactive running, and reports
        whether a particular entry is READY, WAITING, RUNNING, RESETTING,
        FINISHED or NOT_RUN.

        A test group inherits its runtime status from its child entries.
        """
        if self.entries:
            return RuntimeStatus.precedent(
                [entry.runtime_status for entry in self]
            )

        return self._runtime_status

    @runtime_status.setter
    def runtime_status(self, new_status):
        """Set the runtime_status of all child entries."""
        for entry in self:
            entry.runtime_status = new_status
        self._runtime_status = new_status

    def set_runtime_status_filtered(
        self,
        new_status: str,
        entries: Dict,
    ) -> None:
        """
        Alternative setter for the runtime status of an entry. Propagates only
          to the specified entries.

        :param new_status: new runtime status to be set
        :param entries: tree-like structure of entries names
        """
        for entry in self:
            if entry.name in entries.keys():
                if isinstance(entry, TestCaseReport):
                    entry.runtime_status = new_status
                else:
                    entry.set_runtime_status_filtered(
                        new_status, entries[entry.name]
                    )
        self._runtime_status = new_status

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
            rule=Status.STATUS_PRECEDENCE,
        )

    @property
    def counter(self):
        """
        Return counts for each status, will recursively get aggregates from
        children and so on.
        """
        counter = Counter({Status.PASSED: 0, Status.FAILED: 0, "total": 0})

        for child in self:
            if child.category == ReportCategories.ERROR:
                counter.update({Status.ERROR: 1, "total": 1})
            elif child.category == ReportCategories.TASK_RERUN:
                pass
            else:
                counter.update(child.counter)

        return counter

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

        if kwargs.get("__copy", True):
            result.propagate_tag_indices()
        return result

    def filter_cases(
        self, predicate: Callable[["ReportGroup"], bool], is_root: bool = False
    ) -> Self:
        """
        Case-level filter with status retained
        """
        report_obj = copy.deepcopy(self) if is_root else self
        statuses = []
        entries = []

        for entry in report_obj.entries:
            if isinstance(entry, BaseReportGroup):
                statuses.append(entry.status)
                entry = entry.filter_cases(predicate)
                if len(entry):
                    entries.append(entry)
            elif isinstance(entry, TestCaseReport):
                statuses.append(entry.status)
                if predicate(entry):
                    entries.append(entry)
            else:
                raise TypeError(
                    f"Unexpected entry {entry} of type {type(entry)} here."
                )

        report_obj.entries = entries
        report_obj.status_override = Status.precedent(statuses)
        if is_root:
            report_obj.build_index(recursive=True)

        return report_obj

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
                tag_arg_dict=tag_dict, target_tag_dict=obj.tags_index
            )

        return self.filter(_filter_func)

    @property
    def hash(self):
        """
        Generate a hash of this report object, including its entries. This
        hash is used to detect when changes are made under particular nodes
        in the report tree. Since all report entries are mutable, this hash
        should NOT be used to index the report entry in a set or dict - we
        have avoided using the magic __hash__ method for this reason. Always
        use the UID for indexing purposes.

        :return: a hash of all entries in this report group.
        :rtype: ``int``
        """
        return hash(
            (
                self.uid,
                self.status,
                self.runtime_status,
                tuple(entry.hash for entry in self.entries),
            )
        )

    def xfail(self, strict):
        """
        Override report status for test that is marked xfail by user
        :param strict: whether consider XPASS as failure
        """

        if self.failed:
            self.status_override = Status.XFAIL
        elif self.passed:
            if strict:
                self.status_override = Status.XPASS_STRICT
            else:
                self.status_override = Status.XPASS

        # do not override if derived status is UNKNOWN/UNSTABLE

        # propagate xfail down to testcase
        for child in self:
            child.xfail(strict)


class TestReport(BaseReportGroup):
    """
    Report for a Testplan test run, sits at the root of the report tree.
    Only contains TestGroupReports as children.
    """

    def __init__(
        self,
        name,
        meta=None,
        attachments=None,
        information=None,
        timeout=None,
        label=None,
        **kwargs,
    ):
        self._tags_index = None
        self.meta = meta or {}
        self.label = label
        self.information = information or []
        try:
            user = getpass.getuser()
        except (ImportError, OSError):
            # if the USERNAME env variable is unset on Windows, this fails
            # with ImportError
            user = "unknown"
        self.information.extend(
            [
                ("user", user),
                ("command_line_string", " ".join(sys.argv)),
                ("python_version", platform.python_version()),
            ]
        )
        if self.label:
            self.information.append(("label", label))

        # Report attachments: Dict[dst: str, src: str].
        # Maps from destination path (relative from attachments root dir)
        # to the full source path (absolute or relative from cwd).
        self.attachments = attachments or {}
        self.timeout = timeout
        self.category = ReportCategories.TESTPLAN

        super(TestReport, self).__init__(name=name, **kwargs)

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
                *[child.tags_index for child in self]
            )
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
            if getattr(child, "fix_spec_path", None):
                self._bubble_up_fix_spec(child)
            for attachment in child.attachments:
                self.attachments[attachment.dst_path] = attachment.source_path

    def _bubble_up_fix_spec(self, child):
        """Bubble up a "fix_spec_path" from a child report."""
        real_path = child.fix_spec_path
        hash_dir = hashlib.md5(real_path.encode("utf-8")).hexdigest()
        hash_path = os.path.join(
            hash_dir, os.path.basename(child.fix_spec_path)
        )
        child.fix_spec_path = hash_path
        self.attachments[hash_path] = real_path

    def _get_comparison_attrs(self):
        return super(TestReport, self)._get_comparison_attrs() + [
            "tags_index",
            "meta",
        ]

    def serialize(self):
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestReportSchema

        return TestReportSchema().dump(self)

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestReport`` object (and its children)
        from nested python dictionaries.
        """
        from .schemas import TestReportSchema

        return TestReportSchema().load(data)

    def shallow_serialize(self):
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestReportSchema

        return ShallowTestReportSchema().dump(self)

    @classmethod
    def shallow_deserialize(cls, data, old_report):
        """
        Shortcut for deserializing a ``TestReport`` object from its shallow
        serialized representation.
        """
        from .schemas import ShallowTestReportSchema

        deserialized = ShallowTestReportSchema().load(data)
        deserialized.entries = old_report.entries
        deserialized._index = old_report._index

        return deserialized


class TestGroupReport(BaseReportGroup):
    """
    A middle-level container report, can contain both TestGroupReports and
    TestCaseReports.
    """

    def __init__(
        self,
        name,
        category=ReportCategories.TESTGROUP,
        tags=None,
        part=None,
        fix_spec_path=None,
        env_status=None,
        strict_order=False,
        **kwargs,
    ):
        super(TestGroupReport, self).__init__(name=name, **kwargs)

        # This will be used for distinguishing test type (Multitest, GTest
        # etc). Expected to be one of the ReportCategories enum, otherwise
        # the report node will not be correctly rendered in the UI.
        self.category = category

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)

        # A test can be split into many parts and the report of each part
        # can be hold back for merging (if necessary)
        self.part = part  # i.e. (m, n), while 0 <= m < n and n > 1
        self.part_report_lookup = {}

        self.fix_spec_path = fix_spec_path

        if self.entries:
            self.propagate_tag_indices()

        # Expected to be one of ResourceStatus, or None.
        self.env_status = env_status

        # Can be True For group report in category "testsuite"
        self.strict_order = strict_order

        self.covered_lines: Optional[dict] = None

    def __str__(self):
        return (
            f'{self.__class__.__name__}(name="{self.name}", category="{self.category}",'
            f' id="{self.uid}"), tags={self.tags or None})'
        )

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(name="{self.name}", category="{self.category}",'
            f' id="{self.uid}", entries={repr(self.entries)}, tags={self.tags or None})'
        )

    def _get_comparison_attrs(self):
        return super(TestGroupReport, self)._get_comparison_attrs() + [
            "category",
            "tags",
            "tags_index",
        ]

    def append(self, item):
        """Update tag indices if item or self has tag data."""
        super(TestGroupReport, self).append(item)
        if self.tags_index or item.tags_index:
            self.propagate_tag_indices()

    def serialize(self):
        """
        Shortcut for serializing TestGroupReport data to nested python
        dictionaries.
        """
        from .schemas import TestGroupReportSchema

        return TestGroupReportSchema().dump(self)

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestGroupReport`` object
        (and its children) from nested python dictionaries.
        """
        from .schemas import TestGroupReportSchema

        return TestGroupReportSchema().load(data)

    def shallow_serialize(self):
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestGroupReportSchema

        return ShallowTestGroupReportSchema().dump(self)

    @classmethod
    def shallow_deserialize(cls, data, old_report):
        """
        Shortcut for deserializing a ``TestGroupReport`` object from its
        shallow serialized representation.
        """
        from .schemas import ShallowTestGroupReportSchema

        deserialized = ShallowTestGroupReportSchema().load(data)
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
                    child.tags, tags_index
                )

        self.tags_index = tagging.merge_tag_dicts(
            tags_index, self._collect_tag_indices()
        )

    def merge(self, report, strict=True):
        """Propagate tag indices after merge operations."""
        super(TestGroupReport, self).merge(report, strict=strict)
        self.propagate_tag_indices()

    @property
    def attachments(self):
        """Return all attachments from child reports."""
        return itertools.chain.from_iterable(
            child.attachments for child in self
        )

    @property
    def hash(self):
        """
        Generate a hash of this report object, including its entries. This
        hash is used to detect when changes are made under particular nodes
        in the report tree. Since all report entries are mutable, this hash
        should NOT be used to index the report entry in a set or dict - we
        have avoided using the magic __hash__ method for this reason. Always
        use the UID for indexing purposes.

        :return: a hash of all entries in this report group.
        :rtype: ``int``
        """
        return hash(
            (
                self.uid,
                self.status,
                self.runtime_status,
                self.env_status,
                tuple(entry.hash for entry in self.entries),
                tuple(entry["uid"] for entry in self.logs),
            )
        )


class TestCaseReport(Report):
    """
    Leaf of the report tree, contains serialized assertion / log entries.
    """

    exception_logger = ExceptionLogger

    def __init__(
        self,
        name,
        tags=None,
        suite_related=False,
        status_override=None,
        status_reason=None,
        **kwargs,
    ):
        super(TestCaseReport, self).__init__(name=name, **kwargs)

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)
        self.suite_related = suite_related

        self.status_override = status_override
        self.timer = timing.Timer()

        self.attachments = []
        # testcase is default to passed (e.g no assertion)
        self._status = Status.UNKNOWN
        self._runtime_status = RuntimeStatus.READY
        self.category = ReportCategories.TESTCASE
        self.status_reason = status_reason

        self.covered_lines: Optional[dict] = None

    def _get_comparison_attrs(self):
        return super(TestCaseReport, self)._get_comparison_attrs() + [
            "status_override",
            "timer",
            "tags",
            "tags_index",
        ]

    @property
    def passed(self) -> bool:
        """Shortcut for getting if report status should be considered passed."""
        return Status.STATUS_CATEGORY[self.status] == Status.PASSED

    @property
    def failed(self) -> bool:
        """
        Shortcut for checking if report status should be considered failed.
        """
        return Status.STATUS_CATEGORY[self.status] in (
            Status.FAILED,
            Status.ERROR,
        )

    @property
    def unstable(self) -> bool:
        """
        Shortcut for checking if report status should be considered unstable.
        """
        return Status.STATUS_CATEGORY[self.status] == Status.UNSTABLE

    @property
    def unknown(self) -> bool:
        """
        Shortcut for checking if report status is unknown.
        """
        return Status.STATUS_CATEGORY[self.status] == Status.UNKNOWN

    @property
    def status(self) -> Status:
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
        self._status = new_status

    @property
    def runtime_status(self):
        """
        Used for interactive mode, the runtime status of a testcase may be one
        of ``RuntimeStatus``.
        """
        return self._runtime_status

    @runtime_status.setter
    def runtime_status(self, new_status):
        """
        Set the runtime status. As a special case, when a testcase is re-run
        we clear out the assertion entries from any previous run.
        """
        self._runtime_status = new_status
        if self.entries and new_status in (
            RuntimeStatus.RUNNING,
            RuntimeStatus.RESETTING,
        ):
            self.entries = []
            self._status = Status.UNKNOWN
        if new_status == RuntimeStatus.FINISHED:
            self._status = Status.PASSED  # passed if case report has no entry

    # NOTE: this is only for compatibility with the API for filtering.
    def set_runtime_status_filtered(
        self,
        new_status: str,
        entries: Dict,
    ) -> None:
        """
        Alternative setter for the runtime status of an entry, here it is
            equivalent to simply setting the runtime status.

        :param new_status: new runtime status to be set
        :param entries: tree-like structure of entries names, unused, but
            needed for current API compatibility
        """
        self.runtime_status = new_status

    def _assertions_status(self):
        for entry in self:
            if entry.get(Status.PASSED) is False:
                return Status.FAILED
        return Status.PASSED

    def merge(self, report, strict=True):
        """
        TestCaseReport merge overwrites everything in place, as assertions of
        a test case won't be split among different runners. For some special
        test cases, choose the one whose status is of higher precedence.
        """
        self._check_report(report)
        if self.suite_related and Status.precedent(
            [self.status]
        ) < Status.precedent([report.status]):
            return

        self.status_override = report.status_override
        self.runtime_status = report.runtime_status
        self.logs = report.logs
        self.entries = report.entries
        self.timer = report.timer
        self.status_reason = report.status_reason

    def flattened_entries(self, depth):
        """Need to take assertion groups into account."""

        def flatten_dicts(dicts, _depth):
            """Recursively flatten serialized entry list."""
            result = []
            for d in dicts:
                result.append((_depth, d))
                if d["type"] == "Group" or d["type"] == "Summary":
                    result.extend(flatten_dicts(d["entries"], _depth + 1))
            return result

        return flatten_dicts(self.entries, depth)

    def serialize(self):
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema

        return TestCaseReportSchema().dump(self)

    @classmethod
    def deserialize(cls, data):
        """
        Shortcut for instantiating ``TestCaseReport`` object
        from nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema

        return TestCaseReportSchema().load(data)

    @property
    def hash(self):
        """
        Generate a hash of this report object, including its entries. This
        hash is used to detect when changes are made under particular nodes
        in the report tree. Since all report entries are mutable, this hash
        should NOT be used to index the report entry in a set or dict - we
        have avoided using the magic __hash__ method for this reason. Always
        use the UID for indexing purposes.

        :return: a hash of all entries in this report group.
        :rtype: ``int``
        """
        return hash(
            (
                self.uid,
                self.status,
                self.runtime_status,
                tuple(id(entry) for entry in self.entries),
                tuple(entry["uid"] for entry in self.logs),
            )
        )

    def xfail(self, strict):
        """
        Override report status for test that is marked xfail by user
        :param strict: whether consider XPASS as failure
        """
        if self.failed:
            self.status_override = Status.XFAIL
        elif self.passed:
            if strict:
                self.status_override = Status.XPASS_STRICT
            else:
                self.status_override = Status.XPASS

    @property
    def counter(self):
        """
        Return counts for current status.
        """
        counter = Counter({Status.PASSED: 0, Status.FAILED: 0, "total": 0})
        counter.update({self.status: 1, "total": 1})
        return counter

    def pass_if_empty(self):
        """Mark as PASSED if this testcase contains no entries."""
        if not self.entries:
            self._status = Status.PASSED
