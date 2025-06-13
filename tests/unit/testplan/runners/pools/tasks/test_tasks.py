"""Unit test for task classes."""

import os
import sys

import pytest

from testplan.common.serialization import (
    DeserializationError,
    SerializationError,
)
from testplan.runners.pools.tasks import (
    Task,
    TaskMaterializationError,
)

from .data.sample_tasks import RunnableMixin, RunnableTaskAdaptor


class NonRunnableObject:
    """Non runnable."""

    pass


class NonRunnableObjectRunAttr:
    """Non runnable."""

    def __init__(self):
        """TODO."""
        self.run = None


class RunnableThatRaises:
    """Runnable that raises while running."""

    def run(self):
        """Run method."""
        raise RuntimeError("While running.")

    def uid(self):
        """uid method."""
        return "RunnableThatRaises"


class Runnable(RunnableMixin):
    """Runnable."""

    def _run(self):
        """Run method."""
        return sys.maxsize

    def uid(self):
        """uid method."""
        return "Runnable"


class RunnableWithArg(RunnableMixin):
    """Runnable."""

    def __init__(self, number=None):
        """Init."""
        self._number = number

    def _run(self):
        """Run method."""
        return self._number or sys.maxsize

    def uid(self):
        """uid method."""
        return "RunnableWithArg"


def callable_to_runnable():
    """Task target that returns a runnable."""
    return Runnable()


def callable_to_runnable_with_arg(arg):
    """Task target that returns a runnable."""
    return RunnableWithArg(arg)


def callable_to_non_runnable():
    """Task target that returns non runnable."""

    def function():
        """Callable."""
        return sys.maxsize

    return function


def callable_to_none():
    """Task target that returns ``None``."""
    return None


def callable_to_adapted_runnable():
    """TODO."""

    def foo():
        """Callable."""
        return sys.maxsize

    return RunnableTaskAdaptor(foo)


def materialized_task_result(task, expected, serialize=False):
    """TODO."""
    assert isinstance(task, Task)
    materialized = task.materialize()
    if serialize is True:
        serialized = task.dumps()
        task = Task().loads(serialized)
    assert materialized.run().report.val == expected


# pylint: disable=R0201
class TestTaskInitAndMaterialization:
    """TODO."""

    def test_non_runnable_tgt(self):
        """TODO."""
        for task in (
            NonRunnableObject,
            NonRunnableObject(),
            NonRunnableObjectRunAttr,
            NonRunnableObjectRunAttr(),
        ):
            try:
                Task(task).materialize()
            except RuntimeError as exc:
                assert "must have both `run` and `uid` methods" in str(exc)

    def test_runnable_tgt(self):
        """TODO."""
        from .data.sample_tasks import Multiplier

        try:
            materialized_task_result(Task(RunnableThatRaises()), 2)
            raise Exception("Should raise")
        except RuntimeError as exc:
            assert "While running." == str(exc)

        materialized_task_result(Task(Multiplier(2, 3)), 6)
        materialized_task_result(Task(Runnable()), sys.maxsize)
        materialized_task_result(Task(RunnableWithArg(2)), 2)
        task = Task(RunnableTaskAdaptor(lambda x: x * 2, 3))
        materialized_task_result(task, 6)

    def test_string_runnable_tgt_same_module(self):
        """TODO."""
        task = Task("Runnable", module=__name__)
        materialized_task_result(task, sys.maxsize)

        task = Task("RunnableWithArg", module=__name__, args=(2,))
        materialized_task_result(task, 2)

        task = Task("RunnableWithArg", module=__name__, kwargs={"number": 3})
        materialized_task_result(task, 3)

    def test_string_runnable_tgt_other_module(self):
        """TODO."""
        task = Task(
            "Multiplier",
            module="tests.unit.testplan.runners.pools.tasks.data.sample_tasks",
            args=(4,),
        )
        materialized_task_result(task, 8)

        task = Task(
            "Wrapper.InnerMultiplier",
            module="tests.unit.testplan.runners.pools.tasks.data.sample_tasks",
            args=(5,),
        )
        materialized_task_result(task, 10)

        task = Task(
            "sample_tasks.Multiplier",
            module="tests.unit.testplan.runners.pools.tasks.data.relative",
            args=(4,),
            kwargs={"multiplier": 3},
        )
        materialized_task_result(task, 12)

        task = Task(
            "sample_tasks.Wrapper.InnerMultiplier",
            module="tests.unit.testplan.runners.pools.tasks.data.relative",
            args=(5,),
            kwargs={"multiplier": 3},
        )
        materialized_task_result(task, 15)

    def test_callable_to_non_runnable_tgt(self):
        """TODO."""
        from .data.relative import sample_tasks

        for task in (
            Task(callable_to_non_runnable),
            Task(sample_tasks.callable_to_non_runnable, args=(2,)),
            Task(
                "multiply",
                module=(
                    "tests.unit.testplan.runners.pools.tasks.data.sample_tasks"
                ),
                args=(2,),
            ),
            Task(
                "sample_tasks.multiply",
                module="tests.unit.testplan.runners.pools.tasks.data.relative",
                args=(2,),
            ),
        ):
            try:
                task.materialize()
                raise Exception("Should raise.")
            except RuntimeError as exc:
                assert "must have both `run` and `uid` methods" in str(exc)

    def test_callable_to_none(self):
        """TODO."""
        from .data.relative import sample_tasks

        for task in (
            Task(callable_to_none),
            Task(sample_tasks.callable_to_none),
            Task(
                "callable_to_none",
                module=(
                    "tests.unit.testplan.runners.pools.tasks.data.sample_tasks"
                ),
            ),
            Task(
                "sample_tasks.callable_to_none",
                module="tests.unit.testplan.runners.pools.tasks.data.relative",
            ),
        ):
            try:
                task.materialize()
                raise Exception("Should raise.")
            except TaskMaterializationError as exc:
                assert "Cannot get a valid test object from target" in str(exc)

    def test_callable_to_runnable_tgt(self):
        """TODO."""
        task = Task(callable_to_runnable)
        materialized_task_result(task, sys.maxsize)

        task = Task(callable_to_runnable_with_arg, args=(2,))
        materialized_task_result(task, 2)

        from .data import sample_tasks

        task = Task(sample_tasks.callable_to_runnable, args=(2,))
        materialized_task_result(task, 4)

        task = Task(sample_tasks.callable_to_adapted_runnable, args=(2,))
        materialized_task_result(task, 4)

    def test_string_callable_to_runnable_tgt(self):
        """TODO."""
        task = Task("callable_to_runnable", module=__name__)
        materialized_task_result(task, sys.maxsize)

        task = Task(
            "callable_to_runnable_with_arg", module=__name__, args=(2,)
        )
        materialized_task_result(task, 2)

        task = Task(
            "callable_to_runnable",
            module="tests.unit.testplan.runners.pools.tasks.data.sample_tasks",
            args=(2,),
        )
        materialized_task_result(task, 4)

        task = Task(
            "sample_tasks.callable_to_adapted_runnable",
            module="tests.unit.testplan.runners.pools.tasks.data.relative",
            args=(2,),
        )
        materialized_task_result(task, 4)

    def test_path_usage(self):  # pylint: disable=R0201
        """TODO."""
        dirname = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dirname, "data")

        task = Task(
            "Multiplier", module="relative.sample_tasks", args=(4,), path=path
        )
        materialized_task_result(task, 8)

        task = Task(
            "callable_to_runnable",
            module="relative.sample_tasks",
            args=(2,),
            path=path,
        )
        materialized_task_result(task, 4)

        path = os.path.join(path, "relative")

        task = Task("Multiplier", module="sample_tasks", args=(4,), path=path)
        materialized_task_result(task, 8)

        task = Task(
            "callable_to_runnable", module="sample_tasks", args=(2,), path=path
        )
        materialized_task_result(task, 4)


# pylint: disable=R0201
class TestTaskSerialization:
    """TODO."""

    def test_serialize_standard(self):
        """TODO."""
        task = Task("Runnable", module=__name__)
        materialized_task_result(task, sys.maxsize, serialize=True)

        task = Task("RunnableWithArg", module=__name__, args=(2,))
        materialized_task_result(task, 2, serialize=True)

        task = Task("RunnableWithArg", module=__name__, kwargs={"number": 3})
        materialized_task_result(task, 3, serialize=True)

        dirname = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dirname, "data", "relative")
        task = Task("Multiplier", module="sample_tasks", args=(4,), path=path)
        materialized_task_result(task, 8, serialize=True)

    def test_serialize_extended(self):
        task = Task(RunnableTaskAdaptor(lambda x: x * 2, 3))
        materialized_task_result(task, 6, serialize=True)

        task = Task(Runnable)
        materialized_task_result(task, sys.maxsize, serialize=True)

        task = Task(RunnableWithArg(2))
        materialized_task_result(task, 2, serialize=True)

        task = Task(RunnableWithArg, args=(2,))
        materialized_task_result(task, 2, serialize=True)

    def test_raise_on_serialization(self):
        import inspect

        with pytest.raises(
            SerializationError, match=r".*(Cannot|Can't) pickle .*frame.*"
        ):
            t = Task(inspect.currentframe())
            t.dumps()

        with pytest.raises(DeserializationError, match=r".*No data input.*"):
            Task().loads(None)

        with pytest.raises(
            DeserializationError, match=r".*bytes-like.*required.*"
        ):
            Task().loads(inspect.currentframe())
