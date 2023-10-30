"""
Base classes for building a report tree.

The idea behind this module is that we may have parallel
runners for a testplan, each of which would generate a partial report.

Later on these reports would be merged together to
build the final report as the testplan result.
"""
import collections
import copy
import dataclasses
import itertools
import time
import uuid
from typing import Dict, List, Optional, Union

from testplan.common.utils import strings

from .log import create_logging_adapter


class MergeError(Exception):
    """Raised when a merge operation fails."""


class SkipTestcaseException(Exception):
    """Raised from an explicit call to result.skip."""


class ExceptionLogger:
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
    ):
        self.name = name
        self.description = description
        self.definition_name = definition_name or name
        self.uid = uid or name
        self.entries = entries or []

        self.logs = []
        self.logger = create_logging_adapter(report=self)

        # `parent_uids` is a list of the UIDs of all parents of this entry in
        # the report tree. The UIDs are stored with the most distant parent
        # first and the immediate parent last. For example, an entry with
        # parent "A" and grand-parent "B" will have parent_uids = ["B", "A"].
        # This allows any entry to be quickly looked up and updated in the
        # report tree.
        self.parent_uids = parent_uids or []

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
        self._check_report(report)
        # Merge logs
        log_ids = [rec["uid"] for rec in self.logs]
        self.logs += [rec for rec in report.logs if rec["uid"] not in log_ids]

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

    @property
    def hash(self):
        """Return a hash of all entries in this report."""
        return hash((self.uid, tuple(id(entry) for entry in self.entries)))


@dataclasses.dataclass
class EventRecorder:
    name: str
    event_type: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    children: List["EventRecorder"] = dataclasses.field(default_factory=list)

    @classmethod
    def load(
        cls, event_record: Union["EventRecorder", Dict]
    ) -> "EventRecorder":
        if isinstance(event_record, cls):
            return event_record

        event = cls(
            name=event_record["name"],
            event_type=event_record["event_type"],
            start_time=event_record["start_time"],
            end_time=event_record["start_time"],
        )
        if event_record.get("children"):
            for child in event_record["children"]:
                event.children.append(cls.load(child))
        return event

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    def add_child(self, event_executor: "EventRecorder"):
        self.children.append(event_executor)


class ReportGroup(Report):
    """
    A report class that contains other Reports or ReportGroups in `entries`.
    Allows O(1) child report lookup via `get_by_uid` method.
    """

    def __init__(
        self,
        name: str,
        events: Dict = None,
        host: Optional[str] = None,
        **kwargs
    ):
        super(ReportGroup, self).__init__(name=name, **kwargs)

        # Mapping of UID to index in the list of entries.
        self.host: Optional[str] = host
        self._index: Dict = {}
        self._events: Dict[str, EventRecorder] = events or {}
        self.build_index()

        for child in self.entries:
            self.set_parent_uids(child)

    def add_event(
        self, event_executor: EventRecorder, event_id: Optional[str] = None
    ) -> str:
        if event_id is None:
            event_id = uuid.uuid4().hex
        self._events[event_id] = event_executor
        return event_id

    @property
    def events(self) -> Dict[str, Dict]:
        return {k: dataclasses.asdict(v) for k, v in self._events.items()}

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
                if isinstance(child, ReportGroup):
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

    @property
    def entry_uids(self):
        """Return the UIDs of all entries in this report group."""
        return [entry.uid for entry in self]

    def merge_children(self, report, strict=True):
        """
        Merge each children separately, raising ``MergeError`` if `uid`
        does not match.
        """
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

    def merge(self, report, strict=True):
        """Merge child reports first, propagating `strict` flag."""
        self.merge_children(report, strict=strict)
        super(ReportGroup, self).merge(report, strict=strict)

    def append(self, item):
        """Add `item` to `self.entries`, checking type & index."""
        if not isinstance(item, Report):
            raise TypeError(
                "ReportGroup entries must be of "
                "`Report` type, {item} was of: {type} type.".format(
                    item=item, type=type(item)
                )
            )

        if item.uid in self._index:
            raise ValueError(
                "Child report with `uid`: {uid} already exists"
                " in {self}".format(uid=item.uid, self=self)
            )

        super(ReportGroup, self).append(item)
        self._index[item.uid] = len(self.entries) - 1
        self.set_parent_uids(item)

    def set_parent_uids(self, item):
        """
        Set the parent UIDs recursively of an item and its child entries
        after it has been added into this report group.
        """
        item.parent_uids = self.parent_uids + [self.uid]
        if isinstance(item, ReportGroup):
            for child in item.entries:
                item.set_parent_uids(child)

    def extend(self, items):
        """Add `items` to `self.entries`, checking type & index."""
        for item in items:
            self.append(item)

    def filter(self, *functions, **kwargs):
        """Recursively filter report entries and sub-entries."""
        is_root = kwargs.get("__copy", True)
        report_obj = copy.deepcopy(self) if is_root else self

        entries = []
        for entry in report_obj.entries:
            if any(func(entry) for func in functions):

                if isinstance(entry, Report):
                    entry = entry.filter(*functions, __copy=False)
                entries.append(entry)

        report_obj.entries = entries
        if is_root:
            report_obj.build_index(recursive=True)

        return report_obj

    def reset_uid(self, uid=None):
        """
        Reset uid of test report and all of its children, it can be useful
        when need to generate global unique id for each report entry before
        saving, by default strings in standard UUID format will be applied.
        """
        self.uid = uid or strings.uuid4()
        for entry in self:
            if isinstance(entry, (Report, ReportGroup)):
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
                if isinstance(entry, ReportGroup):
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
