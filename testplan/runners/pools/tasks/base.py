"""Tasks and task results base module."""

import copy
import inspect
import os
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from typing import (
    Literal,
    Optional,
    Tuple,
    Union,
    Dict,
    Sequence,
    Callable,
    Any,
)

from testplan.common.entity import Runnable
from testplan.common.serialization import SelectiveSerializable
from testplan.common.utils import strings
from testplan.common.utils.package import import_tmp_module
from testplan.common.utils.path import is_subdir, pwd, rebase_path
from testplan.report import ReportCategories, TestCaseReport, TestGroupReport
from testplan.testing.common import ALL_CASES, AllCaseSelection
from testplan.testing.base import Test, TestResult
from testplan.testing.multitest import MultiTest


CaseSelection = AllCaseSelection | dict[str, AllCaseSelection | list[str]]


# Worker snapshots always expand suite-level ALL_CASES into concrete case IDs.
PlannedCases = AllCaseSelection | dict[str, list[str]]


def collect_planned_cases(test: Test) -> PlannedCases:
    """Capture execution IDs without constructing or modifying reports."""
    if not isinstance(test, MultiTest):
        return ALL_CASES
    return {
        suite.uid(): [case.__name__ for case in cases]
        for suite, cases in test.test_context
    }


def unresolved_selection(
    planned: PlannedCases,
    report: TestGroupReport,
) -> PlannedCases:
    """Select failed/missing cases while retaining terminal case outcomes."""

    def _case_reports(suite: TestGroupReport) -> dict[str, TestCaseReport]:
        """Index expanded testcase reports without including lifecycle hooks."""
        cases: dict[str, TestCaseReport] = {}
        for entry in suite:
            if (
                isinstance(entry, TestCaseReport)
                and entry.category == ReportCategories.TESTCASE
            ):
                cases[entry.uid] = entry
            elif (
                isinstance(entry, TestGroupReport)
                and entry.category == ReportCategories.PARAMETRIZATION
            ):
                cases.update(_case_reports(entry))
        return cases

    if report.category != ReportCategories.MULTITEST:
        return ALL_CASES
    group_unresolved = report.failed or report.unknown
    selection = {}
    suites = {}
    for suite in report:
        if (
            not isinstance(suite, TestGroupReport)
            or suite.category != ReportCategories.TESTSUITE
        ):
            if suite.failed or suite.unknown:
                return ALL_CASES
            continue
        if suite.strict_order:
            return ALL_CASES
        group_unresolved = group_unresolved or suite.failed or suite.unknown
        if any(
            entry.category == ReportCategories.SYNTHESIZED
            and (entry.failed or entry.unknown)
            for entry in suite
        ):
            return ALL_CASES
        suites[suite.uid] = _case_reports(suite)

    expected = (
        planned
        if isinstance(planned, dict)
        else {uid: list(cases) for uid, cases in suites.items()}
    )
    has_terminal_case = False
    for suite_id, case_ids in expected.items():
        cases = suites.get(suite_id, {})
        unresolved = []
        for uid in case_ids:
            case = cases.get(uid)
            if case is None or case.failed or case.unknown:
                unresolved.append(uid)
            elif case.passed or case.xfailed or case.unstable:
                # SKIPPED and XPASS also normalize to UNSTABLE.
                has_terminal_case = True
        if unresolved:
            selection[suite_id] = unresolved
    if not has_terminal_case and group_unresolved:
        return ALL_CASES
    return selection


class TaskMaterializationError(Exception):
    """Error materializing task target to be executed."""


class Task(SelectiveSerializable):
    """
    Container of a target or path to a target that can be materialized into
    a runnable item. The arguments of the Task need to be serializable.

    :param target: A runnable or a string path to a runnable or
                   a callable to a runnable or a string path to a callable
                   to a runnable.
    :param module: Module name that contains the task target definition.
    :param path: Path to module, default is current working directory.
    :param args: Args of target for task materialization.
    :param kwargs: Kwargs of target for task materialization.
    :param uid: Task uid.
    :param rerun: Deprecated alias for ``rerun_limit``. Use ``rerun_limit``
        instead; do not supply both.
    :param rerun_limit: Maximum additional attempts; None inherits the plan
        default.
    :param rerun_entire_task: Rerun the entire original selection when True,
        or only unresolved cases (default). None inherits the plan default.
    :param rerun_on_different_runner: Exclude workers on which this task has
        failed. None inherits the plan default.
    :param case_selection: ALL_CASES, or exact suite IDs mapped to ALL_CASES or lists
        of testcase IDs. Applied after existing filters and partitioning.
    :param weight: Affects task scheduling - the larger the weight, the sooner
        task will be assigned to a worker. Default weight is 0, tasks with the
        same weight will be scheduled in the order they are added.
    :param part: part param that will be propagate to MultiTest
    """

    MAX_RERUN_LIMIT = 3

    def __init__(
        self,
        target: Optional[Union[str, Test]] = None,
        module: Optional[str] = None,
        path: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        uid: Optional[str] = None,
        rerun: int | None = None,
        weight: int = 0,
        part: Optional[Tuple[int, int]] = None,
        rerun_limit: int | None = None,
        rerun_entire_task: bool | None = None,
        rerun_on_different_runner: bool | None = None,
        case_selection: CaseSelection = ALL_CASES,
    ) -> None:
        self._target = target
        self._module = module
        self._path = path or ""
        self._rebased_path = self._path
        self._args = args or tuple()
        self._kwargs = kwargs or dict()
        self._uid = uid or strings.uuid4()
        self._aborted = False
        self._assign_for_rerun = 0
        self._executors: Dict[str, Any] = OrderedDict()
        self.priority = -weight

        if rerun is not None and rerun_limit is not None:
            raise ValueError("Specify only one of rerun and rerun_limit")
        if rerun is not None:
            warnings.warn(
                "Task's rerun parameter is deprecated; use rerun_limit instead.",
                FutureWarning,
                stacklevel=2,
            )
        limit = rerun if rerun is not None else rerun_limit
        if limit is not None:
            if type(limit) is not int or limit < 0:
                raise ValueError("rerun_limit must be a nonnegative integer")
            if limit > self.MAX_RERUN_LIMIT:
                warnings.warn(
                    f"Value of `rerun_limit` cannot exceed {self.MAX_RERUN_LIMIT}"
                )
                limit = self.MAX_RERUN_LIMIT
        for value in (rerun_entire_task, rerun_on_different_runner):
            if value is not None and type(value) is not bool:
                raise ValueError("Rerun switches must be bool or None")
        self._max_rerun_limit = limit
        self._rerun_entire_task: bool | None = rerun_entire_task
        self._rerun_on_different_runner: bool | None = (
            rerun_on_different_runner
        )
        self._case_selection: CaseSelection = ALL_CASES
        self.case_selection = case_selection
        self._failed_runners: set[tuple[str, str]] = set()

        self._part = part

    def __str__(self) -> str:
        if isinstance(self._target, Runnable):
            name = (
                getattr(self._target, "name", None)
                or self._target.__class__.__name__
            )
        else:
            name = self._target

        return f"{self.__class__.__name__}[{name}(uid={self._uid})]"

    @property
    def case_selection(self) -> CaseSelection:
        """Exact suite/case IDs, or ALL_CASES; intersected with existing selection."""
        return self._case_selection

    @case_selection.setter
    def case_selection(self, value: Any) -> None:
        if value is not ALL_CASES:
            if not isinstance(value, dict) or any(
                not isinstance(suite, str)
                or not (
                    cases is ALL_CASES
                    or isinstance(cases, list)
                    and all(isinstance(case, str) for case in cases)
                )
                for suite, cases in value.items()
            ):
                raise ValueError(
                    "case_selection must be ALL_CASES or a mapping of suite IDs "
                    "to ALL_CASES or lists of testcase IDs"
                )
        self._case_selection = copy.deepcopy(value)

    def resolve_rerun_policy(self, config: Any) -> None:
        """Resolve pool defaults once, preserving explicit task overrides."""
        if self._max_rerun_limit is None:
            self._max_rerun_limit = getattr(config, "rerun_limit", 0)
        if self._rerun_entire_task is None:
            self._rerun_entire_task = getattr(
                config, "rerun_entire_task", False
            )
        if self._rerun_on_different_runner is None:
            self._rerun_on_different_runner = getattr(
                config, "rerun_on_different_runner", False
            )

    @property
    def weight(self) -> int:
        return -self.priority

    @weight.setter
    def weight(self, value: int) -> None:
        self.priority = -value

    @property
    def serializable_attrs(self) -> Tuple[str, ...]:
        return (
            "_target",
            "_path",
            "_rebased_path",
            "_args",
            "_kwargs",
            "_module",
            "_uid",
            "_case_selection",
            "_part",
        )

    def uid(self) -> str:
        """Task string uid."""
        return self._uid

    @property
    def args(self) -> Tuple:
        """Task target args."""
        return self._args

    @property
    def kwargs(self) -> Dict:
        """Task target kwargs."""
        return self._kwargs

    @property
    def module(self) -> Optional[str]:
        """Task target module."""
        if callable(self._target):
            return self._target.__module__
        else:
            return self._module

    @property
    def rerun_limit(self) -> int:
        """how many times the task is allowed to rerun."""
        return self._max_rerun_limit or 0

    @property
    def rerun_cnt(self) -> int:
        """how many times the task has been reruned."""
        return self._assign_for_rerun

    @rerun_cnt.setter
    def rerun_cnt(self, value: int) -> None:
        if value < 0:
            raise ValueError("Value of `rerun_cnt` cannot be negative")
        elif value > self.rerun_limit:
            raise ValueError(
                f"Value of `rerun_cnt` cannot exceed {self._max_rerun_limit}"
            )
        self._assign_for_rerun = value

    @property
    def executors(self) -> Dict[str, Any]:
        """Executors to which the task had been assigned."""
        return self._executors

    @property
    def aborted(self) -> bool:
        """Returns if task was aborted."""
        return self._aborted

    def abort(self) -> None:
        """For compatibility reason when task is added into an executor."""
        self._aborted = True

    def materialize(self, target: Any = None) -> Test:
        """
        Create the actual task target executable/runnable object.
        """
        errmsg = "Cannot get a valid test object from target {}"
        target = target or copy.deepcopy(self._target)

        if not isinstance(target, str):
            try:
                run_method = getattr(target, "run")
                if not inspect.ismethod(run_method):
                    raise AttributeError
                uid_method = getattr(target, "uid")
                if not inspect.ismethod(uid_method):
                    raise AttributeError
            except AttributeError:
                if callable(target):
                    inner_target = target(*self._args, **self._kwargs)
                    if inner_target:
                        return self.materialize(inner_target)
                    else:
                        raise TaskMaterializationError(
                            errmsg.format(target.__name__)
                        )
                try:
                    name = target.__class__.__name__
                except:
                    name = target
                raise RuntimeError(
                    f"Target {name} must have both `run` and `uid` methods"
                )
            else:
                if self.case_selection is not ALL_CASES:
                    if not isinstance(target, MultiTest):
                        raise TaskMaterializationError(
                            "case_selection requires a MultiTest target"
                        )
                if isinstance(target, MultiTest):
                    target._task_case_selection = copy.deepcopy(
                        self.case_selection
                    )
                    target.reset_context()

                # propagate part tuple from task to multitest
                if isinstance(target, MultiTest) and self._part:
                    target.set_part(self._part)

                # propagate task discover path from task to Test
                # for task discovery used with a monorepo project
                if self._rebased_path and not is_subdir(
                    self._rebased_path, pwd()
                ):
                    target.set_discover_path(
                        os.path.abspath(self._rebased_path)
                    )

                return target  # type: ignore[no-any-return]
        else:
            target = self._string_to_target()(*self._args, **self._kwargs)
            if target:
                return self.materialize(target)
            else:
                raise TaskMaterializationError(errmsg.format(self._target))

    def _string_to_target(self) -> Any:
        """Dynamically load an object from a module by target name."""

        if self._module is None:
            try:
                if not isinstance(self._target, str):
                    raise TypeError(
                        f"Expected str, got {type(self._target)!r}"
                    )
                module, target = self._target.rsplit(".", 1)
            except ValueError:
                raise TaskMaterializationError(
                    "Task parameters are not sufficient for"
                    f" target {self._target} materialization"
                )
        else:
            module = self._module
            if not isinstance(self._target, str):
                raise TypeError(f"Expected str, got {type(self._target)!r}")
            target = self._target

        with import_tmp_module(
            module, self._rebased_path, warn_if_exist=False
        ) as mod:
            tgt = mod
            for element in target.split("."):
                tgt = getattr(tgt, element, None)
                if tgt is None:
                    raise TaskMaterializationError(
                        f'During materializing target "{self._target}":'
                        f' {tgt} has no attribute "{element}"'
                    )
            return tgt

    def rebase_path(self, local: str, remote: str) -> None:
        """adapt task's path for remote execution if necessary"""
        if os.path.isabs(self._path):
            self._rebased_path = rebase_path(
                self._path,
                local,
                remote,
            )


class TaskResult(SelectiveSerializable):
    """
    Contains result of the executed task target and status/errors/reason
    information that happened during task execution.

    May contain follow up tasks.

    :param planned_cases: Actual suite/case IDs selected before execution,
        or ALL_CASES when unavailable. Independent of mutable scheduling state.
    """

    def __init__(
        self,
        task: Optional[Task] = None,
        result: Optional[TestResult] = None,
        status: bool = False,
        reason: Optional[str] = None,
        follow: Optional[Task] = None,
        planned_cases: PlannedCases = ALL_CASES,
    ):
        self._task: Optional[Task] = task
        self._result: Optional[TestResult] = result
        self._status: bool = status
        self._reason: Optional[str] = reason
        self._follow: Optional[Task] = follow
        self.planned_cases = copy.deepcopy(planned_cases)
        self._uid: str = strings.uuid4()

    def uid(self) -> str:
        """Task result uid"""
        return self._uid

    @property
    def task(self) -> Optional[Task]:
        """Original task."""
        return self._task

    @property
    def result(self) -> Optional[TestResult]:
        """Actual task target result."""
        return self._result

    @property
    def status(self) -> bool:
        """Result status. Should be True on correct successful execution."""
        return self._status

    @property
    def reason(self) -> Optional[str]:
        """Reason for failed status."""
        return self._reason

    @property
    def follow(self) -> Optional[Task]:
        """Follow up tasks that need to be scheduled next."""
        return self._follow

    @property
    def serializable_attrs(self) -> Tuple:
        return (
            "_task",
            "_status",
            "_reason",
            "_result",
            "_follow",
            "_uid",
            "planned_cases",
        )

    def __str__(self) -> str:
        return "TaskResult[{}, {}]".format(self.status, self.reason)


@dataclass
class TaskTargetInformation:
    target_params: Optional[Sequence[Union[Sequence, dict]]]
    multitest_parts: Union[int, str, None]
    task_kwargs: Dict[str, Any]


def task_target(
    parameters: Optional[
        Union[Callable, Sequence[Union[Sequence, dict]]]
    ] = None,
    multitest_parts: Union[int, Literal["auto"], None] = None,
    **kwargs: Any,
) -> Any:
    """
    Decorator to make task target discoverable by plan.schedule_all.

    :param parameters: A collection of parameters to be used to create task
        objects. ``list`` or ``tuple`` entry will be passed to target as
        positional arguments and ``dict`` entry will be passed to target as
        keyword arguments.
    :type parameters: ``list`` or ``tuple`` that contains ``list`` or ``tuple``
        or ``dict``
    :param multitest_parts: The number of multitest parts that will be generated
        from this task target, only applies if the task returns multitest type
    :type multitest_parts: ``int`` or "auto"
    :param kwargs: additional args to Task class, e.g rerun, weight etc.
    :type kwargs: ``dict``
    """

    # `task_target` is used without parentheses, then `parameters` is the
    #  real callable object (task target) to be decorated.
    if callable(parameters) and len(kwargs) == 0:
        func = parameters
        set_task_target(
            func,
            TaskTargetInformation(
                target_params=None,
                multitest_parts=None,
                task_kwargs={},
            ),
        )
        return func

    def inner(func: Callable) -> Callable:
        set_task_target(
            func,
            TaskTargetInformation(
                target_params=parameters,  # type: ignore[arg-type]
                multitest_parts=multitest_parts,
                task_kwargs=kwargs,
            ),
        )

        return func

    return inner


def set_task_target(func: Callable, info: TaskTargetInformation) -> None:
    """
    Mark a callable object as a task target which can be packaged
    in a :py:class:`~testplan.runners.pools.tasks.base.Task` object.
    """
    func.__task_target_info__ = info  # type: ignore[attr-defined]


def is_task_target(func: Callable) -> Any:
    """Check if a callable object is a task target."""
    return getattr(func, "__task_target_info__", False)
