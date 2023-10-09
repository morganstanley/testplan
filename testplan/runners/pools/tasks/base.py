"""Tasks and task results base module."""

import copy
import inspect
import os
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from typing import (
    Optional,
    Tuple,
    Union,
    Dict,
    Sequence,
    Callable,
    Any,
)

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


from testplan.common.entity import Runnable
from testplan.common.serialization import SelectiveSerializable
from testplan.common.utils import strings
from testplan.common.utils.package import import_tmp_module
from testplan.common.utils.path import is_subdir, pwd, rebase_path
from testplan.testing.base import Test, TestResult
from testplan.testing.multitest import MultiTest


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
    :param rerun: Rerun the task up to user specified times until it passes,
        by default 0 (no rerun). To enable task rerun feature, set to positive
        value no greater than 3.
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
        rerun: int = 0,
        weight: int = 0,
        part: Optional[Tuple[int, int]] = None,
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
        self._executors = OrderedDict()
        self.priority = -weight

        if rerun < 0:
            raise ValueError("Value of `rerun` cannot be negative.")
        elif rerun > self.MAX_RERUN_LIMIT:
            warnings.warn(
                "Value of `rerun` cannot exceed {}".format(
                    self.MAX_RERUN_LIMIT
                )
            )
            self._max_rerun_limit = self.MAX_RERUN_LIMIT
        else:
            self._max_rerun_limit = rerun

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
    def weight(self) -> int:
        return -self.priority

    @weight.setter
    def weight(self, value: int):
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
    def module(self) -> str:
        """Task target module."""
        if callable(self._target):
            return self._target.__module__
        else:
            return self._module

    @property
    def rerun(self) -> int:
        """how many times the task is allowed to rerun."""
        return self._max_rerun_limit

    @property
    def reassign_cnt(self) -> int:
        """how many times the task is reassigned for rerun."""
        return self._assign_for_rerun

    @reassign_cnt.setter
    def reassign_cnt(self, value: int):
        if value < 0:
            raise ValueError("Value of `reassign_cnt` cannot be negative")
        elif value > self._max_rerun_limit:
            raise ValueError(
                f"Value of `reassign_cnt` cannot exceed {self._max_rerun_limit}"
            )
        self._assign_for_rerun = value

    @property
    def executors(self):
        """Executors to which the task had been assigned."""
        return self._executors

    @property
    def aborted(self):
        """Returns if task was aborted."""
        return self._aborted

    def abort(self):
        """For compatibility reason when task is added into an executor."""
        self._aborted = True

    def materialize(self, target=None) -> Test:
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

                return target
        else:
            target = self._string_to_target()(*self._args, **self._kwargs)
            if target:
                return self.materialize(target)
            else:
                raise TaskMaterializationError(errmsg.format(self._target))

    def _string_to_target(self):
        """Dynamically load an object from a module by target name."""

        if self._module is None:
            try:
                module, target = self._target.rsplit(".", 1)
            except ValueError:
                raise TaskMaterializationError(
                    "Task parameters are not sufficient for"
                    f" target {self._target} materialization"
                )
        else:
            module = self._module
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

    def rebase_path(self, local, remote):
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
    """

    def __init__(
        self,
        task: Optional[Task] = None,
        result: Optional[TestResult] = None,
        status: bool = False,
        reason: Optional[str] = None,
        follow: Optional[Task] = None,
    ):
        self._task: Optional[Task] = task
        self._result: Optional[TestResult] = result
        self._status: bool = status
        self._reason: Optional[str] = reason
        self._follow: Optional[Task] = follow
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
        return "_task", "_status", "_reason", "_result", "_follow", "_uid"

    def __str__(self):
        return "TaskResult[{}, {}]".format(self.status, self.reason)


class RunnableTaskAdaptor:
    """Minimal callable to runnable task adaptor."""

    __slots__ = ("_target", "_args", "_kwargs")

    def __init__(self, target, *args, **kwargs):
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        """Provide mandatory .run() task method."""
        return self._target(*self._args, **self._kwargs)

    def uid(self):
        """Provide mandatory .uid() task method."""
        return strings.uuid4()


@dataclass
class TaskTargetInformation:
    target_params: Sequence[Union[Sequence, dict]]
    task_kwargs: Dict[str, Any]
    multitest_parts: Union[int, str, None]


def task_target(
    parameters: Union[Callable, Sequence[Union[Sequence, dict]]] = None,
    multitest_parts: Union[int, Literal["auto"], None] = None,
    **kwargs,
):
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
        set_task_target(func, TaskTargetInformation(None, {}, None))
        return func

    def inner(func):
        set_task_target(
            func, TaskTargetInformation(parameters, kwargs, multitest_parts)
        )

        return func

    return inner


def set_task_target(func: Callable, info: TaskTargetInformation):
    """
    Mark a callable object as a task target which can be packaged
    in a :py:class:`~testplan.runners.pools.tasks.base.Task` object.
    """
    func.__task_target_info__ = info


def is_task_target(func):
    """Check if a callable object is a task target."""
    return getattr(func, "__task_target_info__", False)


def get_task_target_information(func) -> TaskTargetInformation:
    return getattr(func, "__task_target_info__")
