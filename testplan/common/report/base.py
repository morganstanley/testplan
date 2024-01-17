"""
Base classes for building a report tree.

The idea behind this module is that we may have parallel
runners for a testplan, each of which would generate a partial report.

Later on these reports would be merged together to
build the final report as the testplan result.
"""
import copy
import uuid
import itertools
import collections
import dataclasses

from testplan.common.utils import strings
from testplan.monitor.event import EventRecorder
import traceback
from collections import Counter
from typing import Dict, List, Optional, Callable
from typing_extensions import Self

from testplan.common.utils import strings, timing
from testplan.common.entity.base import Child
from testplan.testing import tagging

from .log import create_logging_adapter


class MergeError(Exception):
    """Raised when a merge operation fails."""


class SkipTestcaseException(Exception):
    """Raised from an explicit call to result.skip."""


class ExceptionLoggerBase:
    """
    A context manager used for suppressing & logging an exception.
    """

    def __init__(self, *exception_classes, **kwargs):
        self.report = kwargs["report"]
        self.exception_classes = exception_classes or (Exception,)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is not None and issubclass(
            exc_type, self.exception_classes
        ):
            self.report.logger.exception(exc_value)
            return True

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

class Report:
    """
    Base report class, support exception suppression & logging via
    `report.logged_exceptions`. Stores arbitrary objects in `entries` attribute.
    """

    exception_logger = ExceptionLogger

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        definition_name: Optional[str] = None,
        uid: Optional[str] = None,
        entries: Optional[list] = None,
        parent_uids: Optional[List[str]] = None,
        status_override=None,
        status_reason=None,
    ):
        self.name = name
        self.description = description
        self.definition_name = definition_name or name
        self.uid = uid or name
        self.entries = entries or []
        self.status_override = status_override
        self.status_reason = status_reason

        self.logs = []
        self.logger = create_logging_adapter(report=self)

        # `parent_uids` is a list of the UIDs of all parents of this entry in
        # the report tree. The UIDs are stored with the most distant parent
        # first and the immediate parent last. For example, an entry with
        # parent "A" and grand-parent "B" will have parent_uids = ["B", "A"].
        # This allows any entry to be quickly looked up and updated in the
        # report tree.
        self.parent_uids = parent_uids or []

        # Normally, a report group derives its statuses from its child
        # entries. However, in case there are no child entries we use the
        # following values as a fallback.

        # testcase is default to passed (e.g no assertion)
        self._status = Status.UNKNOWN
        self._runtime_status = RuntimeStatus.READY

        self.timer = timing.Timer()

    def __str__(self):
        return '{kls}(name="{name}", uid="{uid}")'.format(
            kls=self.__class__.__name__, name=self.name, uid=self.uid
        )

    def __repr__(self):
        return '{kls}(name="{name}", uid="{uid}", entries={entries})'.format(
            kls=self.__class__.__name__,
            name=self.name,
            uid=self.uid,
            entries=repr(self.entries),
        )

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        return self.entries[key]

    def __getstate__(self):
        # Omitting logger as it is not compatible with deep copy.
        return {k: v for k, v in self.__dict__.items() if k != "logger"}

    def _get_comparison_attrs(self):
        return ["name", "description", "uid", "entries", "logs"]

    def __eq__(self, other):
        for attr in self._get_comparison_attrs():
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __setstate__(self, data):
        data["logger"] = create_logging_adapter(report=self)
        self.__dict__.update(data)

    def logged_exceptions(self, *exception_classes, **kwargs):
        """
        Wrapper around `ExceptionRecorder`, passing `report` arg implicitly.

        Basic usage:

        .. code-block:: python

            with report.logged_exceptions(TypeError, ValueError):
                raise some errors here ...
        """
        kwargs["report"] = self
        return self.exception_logger(*exception_classes, **kwargs)

    def _check_report(self, report):
        """
        Utility method for checking `report` `type` and `definition_name`.
        """
        msg = "Report check failed for `{}` and `{}`. ".format(self, report)

        if report.definition_name != self.definition_name:
            raise AttributeError(
                msg
                + "`definition_name` attributes (`{}`, `{}`) do not match.".format(
                    self.definition_name, report.definition_name
                )
            )

        # We need exact type match, rather than `isinstance` check
        if type(report) != type(self):  # pylint: disable=unidiomatic-typecheck
            raise TypeError(
                msg
                + "Report types (`{}`, `{}`) do not match.".format(
                    type(self), type(report)
                )
            )

    def merge(self, report, strict=True):  # pylint: disable=unused-argument
        """
        Child classes can override this, just make sure `merge`
        operation is idempotent, so that merging the same report onto
        self multiple times does not create extra data.

        :param report: Report that contains logs to merge.
        :type report: ``Report``

        :param strict: Flag for enabling / disabling strict merge ops.
        :type strict: ``bool``
        """
        raise NotImplementedError
        # self._check_report(report)
        # # Merge logs
        # log_ids = [rec["uid"] for rec in self.logs]
        # self.logs += [rec for rec in report.logs if rec["uid"] not in log_ids]

    def append(self, item):
        """Append ``item`` to ``self.entries``, no restrictions."""
        self.entries.append(item)

    def extend(self, items):
        """Extend ``self.entries`` with ``items``, no restrictions."""
        self.entries.extend(items)

    def filter(self, *functions, **kwargs):
        """
        Filtering report's entries in place using the given functions.
        If any of the functions return ``True``
        for a given entry, it will be kept.
        """
        report_obj = self
        if kwargs.get("__copy", True):
            report_obj = copy.deepcopy(self)

        report_obj.entries = [
            e for e in self.entries if any(func(e) for func in functions)
        ]

        return report_obj

    def reset_uid(self, uid=None):
        """
        Reset uid of the report, it can be useful when need to generate
        a global unique id instead of the current one.
        """
        self.uid = uid or strings.uuid4()

    def flattened_entries(self, depth):
        """
        Utility function that is used by `TestGroupReport.flatten`.

        This method should be overridden if `entries` have a custom
        hierarchy instead of a simple list.
        """
        return [(depth, entry) for entry in self]

    def is_empty(self) -> bool:
        """
        Check report is empty or not.
        """
        return len(self.entries) == len(self.logs) == 0

    @property
    def hash(self):
        """Return a hash of all entries in this report."""
        return hash((self.uid, tuple(id(entry) for entry in self.entries)))

#
# @dataclasses.dataclass
# class EventRecorder:
#     name: str
#     event_type: str
#     start_time: Optional[float] = None
#     end_time: Optional[float] = None
#     children: List["EventRecorder"] = dataclasses.field(default_factory=list)
#
#     @classmethod
#     def load(
#         cls, event_record: Union["EventRecorder", Dict]
#     ) -> "EventRecorder":
#         if isinstance(event_record, cls):
#             return event_record
#
#         event = cls(
#             name=event_record["name"],
#             event_type=event_record["event_type"],
#             start_time=event_record["start_time"],
#             end_time=event_record["start_time"],
#         )
#         if event_record.get("children"):
#             for child in event_record["children"]:
#                 event.children.append(cls.load(child))
#         return event
#
#     def __enter__(self):
#         self.start_time = time.time()
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.end_time = time.time()
#
#     def add_child(self, event_executor: "EventRecorder"):
#         self.children.append(event_executor)

class ReportGroup(Report):
    """
    A report class that contains other Reports or ReportGroups in `entries`.
    Allows O(1) child report lookup via `get_by_uid` method.
    """

    exception_logger = ExceptionLogger

    def __init__(self, name, **kwargs):

        super(BaseReportGroup, self).__init__(name=name, **kwargs)

        self._index: Dict = {}
        self.children: List[Child] = []




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
            # TODO: use suite_related flag for now, use synthesized instead
            if not getattr(entry, "suite_related", False):
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
                if hasattr(entry, "set_runtime_status_filtered"):
                    entry.set_runtime_status_filtered(
                        new_status, entries[entry.name]
                    )
                else:
                    entry.runtime_status = new_status

        self._runtime_status = new_status

    def merge_entries(self, report, strict=True):
        """
        For report groups, we call `merge` on each child report
        and later merge basic attributes.

        With default strict=True, ``MergeError`` will be raise if `uid`
        does not match.

        However sometimes original report may not have matching child reports.
        For example this happens when the test target's test cases cannot be
        inspected on initialization time (e.g. GTest).

        In this case we can merge with `strict=False` so that child reports
        are directly appended to original report's entries.
        """
        if strict:
            for entry in report:
                try:
                    self.get_by_uid(entry.uid).merge(entry, strict=strict)
                except KeyError:
                    raise MergeError(
                        "Cannot merge {report} onto {self},"
                        " child report with `uid`: {uid} not found.".format(
                            report=report, self=self, uid=entry.uid
                        )
                    )

        else:
            for entry in report:
                if entry.uid not in self._index:
                    self.append(entry)
                else:
                    self.get_by_uid(entry.uid).merge(entry, strict=strict)

    def merge(self, report, strict=True):
        """Update `status_override` as well."""
        self._check_report(report)

        self.merge_entries(report, strict=strict)

        # Merge logs
        log_ids = [rec["uid"] for rec in self.logs]
        self.logs += [rec for rec in report.logs if rec["uid"] not in log_ids]

        self.timer.merge(report.timer)
        self.children.extend(report.children)

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

        # exclude rerun and synthesized entries from counter
        for child in self:
            if child.category == ReportCategories.ERROR:
                counter.update({Status.ERROR: 1, "total": 1})
            elif child.category in (
                ReportCategories.TASK_RERUN,
                ReportCategories.SYNTHESIZED,
            ):
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
        self,
        predicate: Callable[["BaseReportGroup"], bool],
        is_root: bool = False
    ) -> Self:
        """
        Case-level filter with status retained
        """
        report_obj = copy.deepcopy(self) if is_root else self
        statuses = []
        entries = []

        for entry in report_obj.entries:
            if hasattr(entry, "filter_cases"):
                statuses.append(entry.status)
                entry = entry.filter_cases(predicate)
                if len(entry):
                    entries.append(entry)
            else:
                statuses.append(entry.status)
                if predicate(entry):
                    entries.append(entry)

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

    def build_index(self, recursive=False):
        """
        Build (refresh) indexes for this report and
        optionally for each child report.

        This should be called explicitly if `self.entries` is changed.

        :param recursive: Flag for triggering index build on children.
        :type recursive: ``bool``
        """
        child_ids = [child.uid for child in self]
        dupe_ids = [
            cid
            for cid, count in collections.Counter(child_ids).items()
            if count > 1
        ]

        if dupe_ids:
            raise ValueError(
                "Cannot build index with duplicate uids: `{}`".format(
                    list(dupe_ids)
                )
            )

        self._index = {child.uid: i for i, child in enumerate(self)}

        if recursive:
            for child in self:
                if isinstance(child, BaseReportGroup):
                    child.build_index(recursive=recursive)

    def get_by_uids(self, uids):
        """
        Get child report via a series of `uid` lookup.

        :param uids: A `uid` for the child report.
        :type uids: ``list`` of ``hashable``
        """
        report = self
        for uid in uids:
            report = report.get_by_uid(uid)
        return report

    def get_by_uid(self, uid):
        """
        Get child report via `uid` lookup.

        :param uid: `uid` for the child report.
        :type uid: ``hashable``
        """
        return self.entries[self._index[uid]]

    def has_uid(self, uid):
        """
        Has a child report of `uid`
        """
        return uid in self._index

    def __getitem__(self, uid):
        """Shortcut to `get_by_uid()` method via [] operator."""
        return self.get_by_uid(uid)

    def set_by_uid(self, uid, item):
        """
        Set child report via `uid` lookup.

        If an entry with a matching UID is already present, that entry is
        updated. Otherwise a new entry will be added.

        :param uid: `uid` for the child report.
        :type uid: ``hashable``
        :param item: entry to update or insert into the report.
        :type item: ``Report``
        """
        if uid != item.uid:
            raise ValueError(
                "UIDs don't match: {} != {}".format(uid, item.uid)
            )

        if uid in self._index:
            entry_ix = self._index[uid]
            self.entries[entry_ix] = item
            self.set_parent_uids(item)
        else:
            self.append(item)

    def __setitem__(self, uid, item):
        """Shortcut to `set_by_uid()` method via [] operator."""
        self.set_by_uid(uid, item)

    def set_parent_uids(self, item):
        """
        Set the parent UIDs recursively of an item and its child entries
        after it has been added into this report group.
        """
        item.parent_uids = self.parent_uids + [self.uid]
        if isinstance(item, BaseReportGroup):
            for child in item.entries:
                item.set_parent_uids(child)

    def append(self, item):
        """Add `item` to `self.entries`, checking type & index."""
        if not isinstance(item, Report):
            raise TypeError(
                "BaseReportGroup entries must be of "
                "`Report` type, {item} was of: {type} type.".format(
                    item=item, type=type(item)
                )
            )

        if item.uid in self._index:
            raise ValueError(
                "Child report with `uid`: {uid} already exists"
                " in {self}".format(uid=item.uid, self=self)
            )

        super(BaseReportGroup, self).append(item)
        self._index[item.uid] = len(self.entries) - 1
        self.set_parent_uids(item)

    def extend(self, items):
        """Add `items` to `self.entries`, checking type & index."""
        for item in items:
            self.append(item)

    def reset_uid(self, uid=None):
        """
        Reset uid of test report and all of its children, it can be useful
        when need to generate global unique id for each report entry before
        saving, by default strings in standard UUID format will be applied.
        """
        self.uid = uid or strings.uuid4()
        for entry in self:
            if isinstance(entry, (Report, BaseReportGroup)):
                entry.reset_uid()
        self.build_index()

    def flatten(self, depths=False):
        """
        Depth-first traverse the report tree starting on the leftmost
        node (smallest index), return a list of `(depth, obj)` tuples or
        a list of reports depending on `depths` flag.

        :param depths: Flag for enabling/disabling depth data in result.
        :return: List of reports or list of (`depth`, `report`) tuples.
        """

        def flat_func(rep_obj, depth):
            result = [(depth, rep_obj)]

            for entry in rep_obj:
                if isinstance(entry, BaseReportGroup):
                    result.extend(flat_func(entry, depth + 1))
                elif isinstance(entry, Report):
                    result.append((depth + 1, entry))
                    result.extend(entry.flattened_entries(depth + 2))

            return result

        flattened = flat_func(self, depth=0)

        if depths:
            return flattened
        return list(zip(*flattened))[1]

    @property
    def flattened_logs(self):
        """Return a flattened list of the logs from each Report."""
        return list(
            itertools.chain.from_iterable(
                (rep.logs) for rep in self.flatten() if isinstance(rep, Report)
            )
        )

    @property
    def entry_uids(self):
        """Return the UIDs of all entries in this report group."""
        return [entry.uid for entry in self]


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
    # use for before/after_start/stop, setup, teardown, etc
    SYNTHESIZED = "synthesized"


