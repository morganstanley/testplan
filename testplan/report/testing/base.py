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
import platform
import re
import sys
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import schema
from typing_extensions import Self

from testplan.common.report import (
    BaseReportGroup,
    ExceptionLogger,
    Report,
    ReportCategories,
    RuntimeStatus,
    Status,
)
from testplan.common.report.base import ExceptionLoggerBase
from testplan.common.utils.timing import iana_tz
from testplan.testing import tagging
from testplan.testing.common import TEST_PART_PATTERN_FORMAT_STRING

TESTCASE_XFAIL_CONDITION_SCHEMA = schema.Schema(
    schema.And(
        {
            schema.Optional("error"): schema.Use(re.compile),
            schema.Optional("failed"): {
                "type": str,
                "description": schema.Use(re.compile),
            },
        },
        schema.Or(
            lambda d: "error" in d and len(d) == 1,
            lambda d: "failed" in d and len(d) == 1,
        ),
    )
)


class TestReport(BaseReportGroup):
    """
    Report for a Testplan test run, sits at the root of the report tree.
    Only contains TestGroupReports as children.
    """

    def __init__(
        self,
        name: str,
        meta: Optional[Dict[str, Any]] = None,
        attachments: Optional[Dict[str, str]] = None,
        information: Optional[List[Tuple[str, str]]] = None,
        timeout: Optional[int] = None,
        label: Optional[str] = None,
        timezone: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self._tags_index: Optional[Dict[str, Any]] = None
        self.meta = meta or {}
        self.label = label
        self.information = information or []
        self.resource_meta_path: Optional[str] = None

        # reports coming from tpr already have certain info set
        info_keys = [info[0] for info in self.information]
        if "user" not in info_keys:
            try:
                user = getpass.getuser()
            except (ImportError, OSError):
                # if the USERNAME env variable is unset on Windows, this fails
                # with ImportError
                user = "unknown"
            self.information.append(("user", user))
        if "command_line_string" not in info_keys:
            self.information.append(
                ("command_line_string", " ".join(sys.argv))
            )
        if "python_version" not in info_keys:
            self.information.append(
                ("python_version", platform.python_version())
            )
        if self.label and "label" not in info_keys:
            self.information.append(("label", self.label))

        # Report attachments: Dict[dst: str, src: str].
        # Maps from destination path (relative from attachments root dir)
        # to the full source path (absolute or relative from cwd).
        self.attachments = attachments or {}
        self.timeout = timeout
        self.category = ReportCategories.TESTPLAN

        # Timezone of testplan's runner
        # NOTE: caller within tpsreport should always have this field set
        self.timezone: str = timezone or iana_tz()

        super(TestReport, self).__init__(name=name, **kwargs)

    @property
    def tags_index(self) -> Dict[str, Any]:
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

    def propagate_tag_indices(self) -> None:
        """
        TestReport does not have native tag data,
        so it just triggers children's tag updates.
        """
        for child in self:
            child.propagate_tag_indices()

        # reset tags index, so it gets repopulated on the next call
        self._tags_index = None

    def bubble_up_attachments(self) -> None:
        """
        Attachments are saved at various levels of the report:

          * Fix spec file attached to multitests.
          * When implemented result.attach will attach files to assertions.

        This iterates through the report entries and bubbles up all the
        attachments to the top level. This top level dictionary of attachments
        will be used by Exporters to export attachments as well as the report.
        """
        for child in self:
            for attachment in child.attachments:
                self.attachments[attachment.dst_path] = attachment.source_path

    def _get_comparison_attrs(self) -> List[str]:
        return super(TestReport, self)._get_comparison_attrs() + [
            "tags_index",
            "meta",
        ]

    def serialize(self) -> Dict[str, Any]:
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestReportSchema

        return TestReportSchema().dump(self)  # type: ignore[no-any-return]

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TestReport":
        """
        Shortcut for instantiating ``TestReport`` object (and its children)
        from nested python dictionaries.
        """
        from .schemas import TestReportSchema

        return TestReportSchema().load(data)  # type: ignore[no-any-return]

    def shallow_serialize(self) -> Dict[str, Any]:
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestReportSchema

        return ShallowTestReportSchema().dump(self)  # type: ignore[no-any-return]

    @classmethod
    def shallow_deserialize(
        cls, data: Dict[str, Any], old_report: "TestReport"
    ) -> "TestReport":
        """
        Shortcut for deserializing a ``TestReport`` object from its shallow
        serialized representation.
        """
        from .schemas import ShallowTestReportSchema

        deserialized: TestReport = ShallowTestReportSchema().load(data)
        deserialized.entries = old_report.entries
        deserialized._index = old_report._index

        return deserialized

    def filter(self, *functions: Callable[..., bool], **kwargs: Any) -> Self:
        """
        Tag indices are updated after filter operations.
        """
        result = super(TestReport, self).filter(*functions, **kwargs)

        # We'd like to call tag propagation before returning the root node,
        # so we rely on absence of implicit `__copy` arg to decide if we should
        # trigger tag index propagation or not. If we don't do this check
        # then tag propagation will be called for each filter call on
        # sub-nodes which is going to be a redundant operation.

        if kwargs.get("__copy", True):
            result.propagate_tag_indices()
        return result

    def inherit(self, deceased: Self) -> Self:
        self.timer = deceased.timer
        self.status_override = deceased.status_override
        self.status_reason = deceased.status_reason
        self.attachments = deceased.attachments
        self.logs = deceased.logs

        for uid in set(self.entry_uids) & set(deceased.entry_uids):
            self_ = self[uid]
            deceased_ = deceased[uid]
            if isinstance(self_, TestGroupReport) and isinstance(
                deceased_, TestGroupReport
            ):
                self_.inherit(deceased_)

        return self


class TestGroupReport(BaseReportGroup):
    """
    A middle-level container report, can contain both TestGroupReports and
    TestCaseReports.
    """

    def __init__(
        self,
        name: str,
        category: str = ReportCategories.TESTGROUP,
        tags: Optional[Union[Dict[str, Any], str]] = None,
        part: Optional[Tuple[int, int]] = None,
        env_status: Optional[str] = None,
        strict_order: bool = False,
        timezone: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super(TestGroupReport, self).__init__(name=name, **kwargs)

        # This will be used for distinguishing test type (Multitest, GTest
        # etc). Expected to be one of the ReportCategories enum, otherwise
        # the report node will not be correctly rendered in the UI.
        self.category = category

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)

        # A test can be split into many parts and the report of each part
        # can be hold back for merging (if necessary)
        # this is a multitest only feature
        self.part = part  # i.e. (m, n), while 0 <= m < n and n > 1
        self.part_report_lookup: Dict[int, "TestGroupReport"] = {}

        if self.entries:
            self.propagate_tag_indices()

        # Expected to be one of ResourceStatus, or None.
        self.env_status = env_status

        # Can be True For group report in category "testsuite"
        self.strict_order = strict_order

        # Timezone of test's executor (Test-level only)
        # NOTE: caller within tpsreport should always have this field set
        self.timezone: str = timezone or iana_tz()

        # Host of test's executor (Test-level only)
        self.host: Optional[str] = None

        self.covered_lines: Optional[dict] = None

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}(name="{self.name}", category="{self.category}",'
            f' id="{self.uid}"), tags={self.tags or None})'
        )

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(name="{self.name}", category="{self.category}",'
            f' id="{self.uid}", entries={repr(self.entries)}, tags={self.tags or None})'
        )

    def _get_comparison_attrs(self) -> List[str]:
        return super(TestGroupReport, self)._get_comparison_attrs() + [
            "category",
            "tags",
            "tags_index",
        ]

    def append(self, item: Report) -> None:
        """Update tag indices if item or self has tag data."""
        super(TestGroupReport, self).append(item)
        if self.tags_index or getattr(item, "tags_index", None):
            self.propagate_tag_indices()

    def serialize(self) -> Dict[str, Any]:
        """
        Shortcut for serializing TestGroupReport data to nested python
        dictionaries.
        """
        from .schemas import TestGroupReportSchema

        return TestGroupReportSchema().dump(self)  # type: ignore[no-any-return]

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TestGroupReport":
        """
        Shortcut for instantiating ``TestGroupReport`` object
        (and its children) from nested python dictionaries.
        """
        from .schemas import TestGroupReportSchema

        return TestGroupReportSchema().load(data)  # type: ignore[no-any-return]

    def shallow_serialize(self) -> Dict[str, Any]:
        """Shortcut for shallow-serializing test report data."""
        from .schemas import ShallowTestGroupReportSchema

        return ShallowTestGroupReportSchema().dump(self)  # type: ignore[no-any-return]

    @classmethod
    def shallow_deserialize(
        cls, data: Dict[str, Any], old_report: "TestGroupReport"
    ) -> "TestGroupReport":
        """
        Shortcut for deserializing a ``TestGroupReport`` object from its
        shallow serialized representation.
        """
        from .schemas import ShallowTestGroupReportSchema

        deserialized: TestGroupReport = ShallowTestGroupReportSchema().load(
            data
        )
        deserialized.entries = old_report.entries
        deserialized._index = old_report._index
        return deserialized

    def _collect_tag_indices(self) -> Dict[str, Any]:
        """
        Recursively collect tag indices from children (and their children etc)
        """
        tag_dicts = [self.tags]

        for child in self:
            if isinstance(child, TestGroupReport):
                tag_dicts.append(child._collect_tag_indices())
            elif isinstance(child, TestCaseReport):
                tag_dicts.append(child.tags)
        return tagging.merge_tag_dicts(*tag_dicts)  # type: ignore[no-any-return]

    def propagate_tag_indices(
        self, parent_tags: Optional[Dict[str, Any]] = None
    ) -> None:
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

    def merge(self, report: "TestGroupReport", strict: bool = True) -> None:  # type: ignore[override]
        """Propagate tag indices after merge operations."""
        super().merge(report, strict=strict)
        self.propagate_tag_indices()

        # XXX:
        # merge report itself could be a bad idea, if for ui display purpose
        # we'd rather do it in web-ui frontend instead
        if self.timezone is None:
            self.timezone = report.timezone

    @property
    def attachments(self) -> "itertools.chain[Any]":
        """Return all attachments from child reports."""
        return itertools.chain.from_iterable(
            child.attachments for child in self
        )

    @property
    def hash(self) -> int:
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

    def filter(self, *functions: Callable[..., bool], **kwargs: Any) -> Self:
        """
        Tag indices are updated after filter operations.
        """
        result = super(TestGroupReport, self).filter(*functions, **kwargs)

        # We'd like to call tag propagation before returning the root node,
        # so we rely on absence of implicit `__copy` arg to decide if we should
        # trigger tag index propagation or not. If we don't do this check
        # then tag propagation will be called for each filter call on
        # sub-nodes which is going to be a redundant operation.

        if kwargs.get("__copy", True):
            result.propagate_tag_indices()
        return result

    def inherit(self, deceased: Self) -> Self:
        self.timer = deceased.timer
        self.status_override = deceased.status_override
        self.status_reason = deceased.status_reason
        self.env_status = deceased.env_status
        self.logs = deceased.logs

        for uid in set(self.entry_uids) & set(deceased.entry_uids):
            self_ = self[uid]
            deceased_ = deceased[uid]
            if isinstance(self_, TestGroupReport) and isinstance(
                deceased_, TestGroupReport
            ):
                self_.inherit(deceased_)
            elif isinstance(self_, TestCaseReport) and isinstance(
                deceased_, TestCaseReport
            ):
                self_.inherit(deceased_)

        return self

    def annotate_part_num(self) -> None:
        # NOTE: part is only set at mt level, meth is for mt-level report only
        if not self.part:
            return
        _wrap = lambda s: TEST_PART_PATTERN_FORMAT_STRING.format(
            s, self.part[0], self.part[1]
        )
        for e in self.pre_order_iterate():
            if (
                isinstance(e, TestCaseReport)
                and e.category == ReportCategories.SYNTHESIZED
            ):
                # assuming specially names are in backend only
                e.uid = _wrap(e.uid)
                e.name = _wrap(e.name)
        # NOTE: synthesized tc not only exists in synthesized ts
        self.build_index(recursive=True)


class TestCaseReport(Report):
    """
    Leaf of the report tree, contains serialized assertion / log entries.
    """

    exception_logger = ExceptionLogger

    def __init__(
        self,
        name: str,
        tags: Optional[Union[Dict[str, Any], str]] = None,
        category: str = ReportCategories.TESTCASE,
        **kwargs: Any,
    ) -> None:
        super(TestCaseReport, self).__init__(name=name, **kwargs)

        self.tags = tagging.validate_tag_value(tags) if tags else {}
        self.tags_index = copy.deepcopy(self.tags)
        self.attachments: List[Any] = []
        self.category = category
        self.covered_lines: Optional[dict] = None

    def _get_comparison_attrs(self) -> List[str]:
        return super(TestCaseReport, self)._get_comparison_attrs() + [
            "status_override",
            "timer",
            "tags",
            "tags_index",
        ]

    @Report.status.getter  # type: ignore[attr-defined]
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

    @Report.runtime_status.setter  # type: ignore[attr-defined]
    def runtime_status(self, new_status: RuntimeStatus) -> None:
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

    def _assertions_status(self) -> Status:
        # entries already serialized here
        for entry in self:
            if entry.get("passed") is False:
                return Status.FAILED
        return Status.PASSED

    def merge(self, report: "TestCaseReport", strict: bool = True) -> None:  # type: ignore[override]
        """
        TestCaseReport merge overwrites everything in place, as assertions of
        a test case won't be split among different runners. For some special
        test cases, choose the one whose status is of higher precedence.
        """
        self._check_report(report)
        if (
            self.category == ReportCategories.SYNTHESIZED
            and self.status.precede(report.status)
        ):
            return

        self.status_override = Status.precedent(
            [self.status_override, report.status_override]
        )
        self.runtime_status = report.runtime_status
        self.logs = report.logs
        self.entries = report.entries
        self.timer = report.timer
        self.status_reason = report.status_reason

    def flattened_entries(
        self, depth: int
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """Need to take assertion groups into account."""

        def flatten_dicts(
            dicts: List[Dict[str, Any]], _depth: int
        ) -> List[Tuple[int, Dict[str, Any]]]:
            """Recursively flatten serialized entry list."""
            result = []
            for d in dicts:
                result.append((_depth, d))
                if d["type"] == "Group" or d["type"] == "Summary":
                    result.extend(flatten_dicts(d["entries"], _depth + 1))
            return result

        return flatten_dicts(self.entries, depth)

    def serialize(self) -> Dict[str, Any]:
        """
        Shortcut for serializing test report data
        to nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema

        return TestCaseReportSchema().dump(self)  # type: ignore[no-any-return]

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TestCaseReport":
        """
        Shortcut for instantiating ``TestCaseReport`` object
        from nested python dictionaries.
        """
        from .schemas import TestCaseReportSchema

        return TestCaseReportSchema().load(data)  # type: ignore[no-any-return]

    @property
    def hash(self) -> int:
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

    def xfail(self, strict: bool, condition: Optional[dict]) -> None:
        """
        Override report status for test that is marked xfail by user
        :param strict: whether consider XPASS as failure
        """
        if self.failed and self._xfail_match_condition(condition):
            self.status_override = Status.XFAIL
        elif self.passed and self._xfail_partial_match_condition(condition):
            if strict:
                self.status_override = Status.XPASS_STRICT
            else:
                self.status_override = Status.XPASS

    @staticmethod
    def _xfail_match_assertion(exp: dict, val: dict) -> bool:
        if not isinstance(val, dict):
            return False
        for k, v in exp.items():
            if k not in val:
                return False
            actual = val[k]
            if isinstance(v, re.Pattern):
                if not isinstance(actual, str) or not v.search(actual):
                    return False
            elif isinstance(v, dict):
                if not TestCaseReport._xfail_match_assertion(v, actual):
                    return False
            elif actual != v:
                return False
        return True

    def _xfail_match_condition(self, condition: Optional[dict]) -> bool:
        if not condition:
            return True

        if "error" in condition:
            return self.status == Status.ERROR and any(
                condition["error"].search(log_record.get("message", ""))
                for log_record in self.logs
            )
        return any(
            TestCaseReport._xfail_match_assertion(condition["failed"], entry)
            for entry in self.entries
            if entry.get("passed") is False
        )

    def _xfail_partial_match_condition(
        self, condition: Optional[dict]
    ) -> bool:
        if not condition:
            return True

        if "error" in condition:
            return any(
                condition["error"].search(log_record.get("message", ""))
                for log_record in self.logs
            )
        return any(
            TestCaseReport._xfail_match_assertion(condition["failed"], entry)
            for entry in self.entries
        )

    @property
    def counter(self) -> Counter:
        """
        Return counts for current status.
        """
        counter = Counter(
            {
                Status.PASSED.to_json_compatible(): 0,
                Status.FAILED.to_json_compatible(): 0,
                "total": 0,
            }
        )
        counter.update({self.status.to_json_compatible(): 1, "total": 1})
        return counter

    def pass_if_empty(self) -> None:
        """Mark as PASSED if this testcase contains no entries."""
        if not self.entries:
            self._status = Status.PASSED

    def inherit(self, deceased: Self) -> Self:
        self.timer = deceased.timer
        self.runtime_status = deceased.runtime_status
        self.status = deceased.status
        self.status_override = deceased.status_override
        self.status_reason = deceased.status_reason
        self.attachments = deceased.attachments
        self.logs = deceased.logs
        self.entries = deceased.entries
        return self
