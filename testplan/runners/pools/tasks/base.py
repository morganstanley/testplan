"""Tasks and task results base module."""

import sys
import six
import uuid
import inspect
import warnings
import importlib
from collections import OrderedDict

from six.moves import cPickle
import copy


class TaskMaterializationError(Exception):
    """Error materializing task target to be executed."""


class TaskSerializationError(Exception):
    """Error on serializing task."""


class TaskDeserializationError(Exception):
    """Error on de-serializing task."""


class Task(object):
    """
    Container of a target or path to a target that can be materialized into
    a runnable item. The arguments of the Task need to be serializable.

    .. code-block:: python

      # Object with .run() method.
      Task(Runnable(arg1, arg2=False))

      # On same python module.
      Task(Runnable(arg1, arg2=False), module=__name__)

      # Target is a class with .run() method.
      Task('Multiplier', module='tasks.data.sample_tasks', args=(5,))

      # Similar but lives in specific path.
      Task('sample_tasks.Multiplier', args=(4,), path='../path/to/module')

      # Target is a callable function that returns a runnable object.
      Task('module.sub.generate_runnable',
           args=(args1,), kwargs={'args2': False})

    :param target: A runnable or a string path to a runnable or
                   a callable to a runnable or a string path to a callable
                   to a runnable.
    :type target: ``str`` path or runnable ``object``
    :param module: Module name that contains the task target definition.
    :type module: ``str``
    :param path: Path to module.
    :type path: ``str``
    :param args: Args of target for task materialization.
    :type args: ``tuple``
    :param kwargs: Kwargs of target for task materialization.
    :type kwargs: ``kwargs``
    :param uid: Task uid.
    :type uid: ``str``
    :param rerun: Rerun the task up to user specified times unless it passes,
        by default 0 (no rerun). To enable task rerun feature, this value can
        be at most 3.
    :type rerun: ``int``
    """

    MAX_RERUN_LIMIT = 3

    def __init__(
        self,
        target=None,
        module=None,
        path=None,
        args=None,
        kwargs=None,
        uid=None,
        rerun=0,
    ):
        self._target = target
        self._module = module
        self._path = path
        self._args = args or tuple()
        self._kwargs = kwargs or dict()
        self._uid = uid or str(uuid.uuid4())
        self._max_rerun_limit = (
            self.MAX_RERUN_LIMIT
            if rerun > self.MAX_RERUN_LIMIT
            else int(rerun)
        )
        self._assign_for_rerun = 0
        self._executors = OrderedDict()

        if self._max_rerun_limit < 0:
            raise ValueError("Value of `rerun` cannot be negative.")
        elif self._max_rerun_limit > self.MAX_RERUN_LIMIT:
            warnings.warn(
                "Value of `rerun` cannot exceed {}".format(
                    self.MAX_RERUN_LIMIT
                )
            )
            self._max_rerun_limit = self.MAX_RERUN_LIMIT

    def __str__(self):
        return "{}[{}]".format(self.__class__.__name__, self._uid)

    @property
    def all_attrs(self):
        return ("_target", "_path", "_args", "_kwargs", "_module", "_uid")

    def uid(self):
        """Task string uid."""
        return self._uid

    @property
    def name(self):
        """Task name."""
        if not isinstance(self._target, six.string_types):
            try:
                name = self._target.__class__.__name__
            except AttributeError:
                name = self._target
        else:
            name = self._target
        return "Task[{}]".format(name)

    @property
    def args(self):
        """Task target args."""
        return self._args

    @property
    def kwargs(self):
        """Task target kwargs."""
        return self._kwargs

    @property
    def module(self):
        """Task target module."""
        if callable(self._target):
            return self._target.__module__
        else:
            return self._module

    @property
    def rerun(self):
        """how many times the task is allowed to rerun."""
        return self._max_rerun_limit

    @property
    def reassign_cnt(self):
        """how many times the task is reassigned for rerun."""
        return self._assign_for_rerun

    @reassign_cnt.setter
    def reassign_cnt(self, value):
        if value < 0:
            raise ValueError("Value of `reassign_cnt` cannot be negative")
        elif value > self.MAX_RERUN_LIMIT:
            raise ValueError(
                "Value of `reassign_cnt` cannot exceed {}".format(
                    self.MAX_RERUN_LIMIT
                )
            )
        self._assign_for_rerun = value

    @property
    def executors(self):
        """Executors to which the task had been assigned."""
        return self._executors

    def materialize(self, target=None):
        """
        Create the actual task target executable/runnable/callable object.
        """
        target = target or copy.deepcopy(self._target)
        if not isinstance(target, six.string_types):
            try:
                run_method = getattr(target, "run")
                if not inspect.ismethod(run_method):
                    raise AttributeError
            except AttributeError:
                if callable(target):
                    return self.materialize(
                        target(*self._args, **self._kwargs)
                    )
                try:
                    name = target.__class__.__name__
                except:
                    name = target
                raise RuntimeError(
                    ("Task {} must have a " ".run() method.").format(name)
                )
            else:
                return target
        else:
            target = self._string_to_target()
            return self.materialize(target(*self._args, **self._kwargs))

    def _string_to_target(self):
        path_inserted = False
        if isinstance(self._path, six.string_types):
            sys.path.insert(0, self._path)
            path_inserted = True

        elements = self._target.split(".")
        target_src = elements.pop(-1)
        try:
            if len(elements):
                mod = importlib.import_module(".".join(elements))
                target = getattr(mod, target_src)
            else:
                if self._module is None:
                    msg = (
                        "Task parameters are not sufficient "
                        "for target {} materialization".format(self._target)
                    )
                    raise TaskMaterializationError(msg)
                mod = importlib.import_module(self._module)
                target = getattr(mod, self._target)
        finally:
            if path_inserted is True:
                sys.path.remove(self._path)
        return target

    def dumps(self, check_loadable=False):
        """Serialize a task."""
        data = {}
        for attr in self.all_attrs:
            data[attr] = getattr(self, attr)
        try:
            serialized = cPickle.dumps(data)
            if check_loadable is True:
                cPickle.loads(serialized)
            return serialized
        except Exception as exc:
            raise TaskSerializationError(str(exc))

    def loads(self, obj):
        """De-serialize a dumped task."""
        try:
            data = cPickle.loads(obj)
        except Exception as exc:
            raise TaskDeserializationError(str(exc))
        for attr, value in data.items():
            setattr(self, attr, value)
        return self


class TaskResult(object):
    """
    Contains result of the executed task target and status/errors/reason
    information that happened during task execution.

    May contain follow up tasks.
    """

    def __init__(
        self, task=None, result=None, status=False, reason=None, follow=None
    ):
        self._task = task
        self._result = result
        self._status = status
        self._reason = reason
        self._follow = follow
        self._uid = str(uuid.uuid4())

    def uid(self):
        """Task result uid"""
        return self._uid

    @property
    def task(self):
        """Original task."""
        return self._task

    @property
    def result(self):
        """Actual task target result."""
        return self._result

    @property
    def status(self):
        """Result status. Should be True on correct successful execution."""
        return self._status

    @property
    def reason(self):
        """Reason for failed status."""
        return self._reason

    @property
    def follow(self):
        """Follow up tasks that need to be scheduled next."""
        return self._follow

    @property
    def all_attrs(self):
        return ("_task", "_status", "_reason", "_result", "_follow", "_uid")

    def dumps(self, check_loadable=False):
        """Serialize a task result."""
        data = {}
        for attr in self.all_attrs:
            data[attr] = getattr(self, attr)
        try:
            serialized = cPickle.dumps(data)
            if check_loadable is True:
                cPickle.loads(serialized)
            return serialized
        except Exception as exc:
            raise TaskSerializationError(str(exc))

    def loads(self, obj):
        """De-serialize a dumped task result."""
        try:
            data = cPickle.loads(obj)
        except Exception as exc:
            raise TaskDeserializationError(str(exc))
        for attr, value in data.items():
            setattr(self, attr, value)
        return self

    def __str__(self):
        return "TaskResult[{}, {}]".format(self.status, self.reason)


class RunnableTaskAdaptor(object):
    """Minimal callable to runnable task adaptor."""

    __slots__ = ("_target", "_args", "_kwargs")

    def __init__(self, target, *args, **kwargs):
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        """Provide mandatory .run() task method."""
        return self._target(*self._args, **self._kwargs)
