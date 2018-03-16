"""Unit test for task classes."""

import os
from testplan.runners.pools.tasks import (Task, RunnableTaskAdaptor,
                                          TaskDeserializationError,
                                          TaskSerializationError)


class NonRunnableObject(object):
    """Non runnable."""

    pass


class NonRunnableObjectRunAttr(object):
    """Non runnable."""

    def __init__(self):
        """TODO."""
        self.run = None


class RunnableThatRaises(object):
    """Runnable that raises while running."""

    def run(self):
        """Run method."""
        raise RuntimeError('While running.')


class Runnable(object):
    """Runnable."""

    def run(self):
        """Run method."""
        import sys
        return sys.maxsize


class RunnableWithArg(object):
    """Runnable."""

    def __init__(self, number=None):
        """Init."""
        self._number = number

    def run(self):
        """Run method."""
        import sys
        return self._number or sys.maxsize


def callable_to_runnable():
    """Task target that returns a runnable."""
    return Runnable()


def callable_to_runnable_with_arg(arg):
    """Task target that returns a runnable."""
    return RunnableWithArg(arg)


def callable_to_non_runnable():
    """Task target that returns non runnable."""
    import sys

    def function():
        """Callable."""
        return sys.maxsize
    return function


def callable_to_adapted_runnable():
    """TODO."""
    import sys
    from testplan.runners.pools.tasks import RunnableTaskAdaptor

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
    assert materialized.run() == expected


# pylint: disable=R0201
class TestTaskInitAndMaterialization(object):
    """TODO."""

    def test_non_runnable_tgt(self):  # pylint: disable=R0201
        """TODO."""
        for task in (NonRunnableObject, NonRunnableObject(),
                     NonRunnableObjectRunAttr, NonRunnableObjectRunAttr()):
            try:
                Task(task).materialize()
            except RuntimeError as exc:
                assert 'must have a .run() method' in str(exc)

    def test_runnable_tgt(self):  # pylint: disable=R0201
        """TODO."""
        import sys
        from .data.sample_tasks import Multiplier
        try:
            materialized_task_result(Task(RunnableThatRaises()), 2)
            raise Exception('Should raise')
        except RuntimeError as exc:
            assert 'While running.' == str(exc)

        materialized_task_result(Task(Multiplier(2, 3)), 6)
        materialized_task_result(Task(Runnable()), sys.maxsize)
        materialized_task_result(Task(RunnableWithArg(2)), 2)
        task = Task(RunnableTaskAdaptor(lambda x: x * 2, 3))
        materialized_task_result(task, 6)

    def test_string_runnable_tgt_same_module(self):
        """TODO."""
        import sys
        task = Task('Runnable', module=__name__)
        materialized_task_result(task, sys.maxsize)

        task = Task('RunnableWithArg', module=__name__, args=(2,))
        materialized_task_result(task, 2)

        task = Task('RunnableWithArg', module=__name__, kwargs={'number': 3})
        materialized_task_result(task, 3)

    def test_string_runnable_tgt_other_module(self):
        """TODO."""
        task = Task('tasks.data.sample_tasks.Multiplier', args=(4,))
        materialized_task_result(task, 8)

        task = Task('Multiplier', module='tasks.data.sample_tasks',
                    args=(5,))
        materialized_task_result(task, 10)

        task = Task('tasks.data.sample_tasks.Multiplier',
                    args=(4,), kwargs={'multiplier': 3})
        materialized_task_result(task, 12)

    def test_callable_to_non_runnable_tgt(self):  # pylint: disable=R0201
        """TODO."""
        from .data.relative import sample_tasks
        for task in (Task(callable_to_non_runnable),
                     Task(sample_tasks.callable_to_non_runnable,
                          args=(2,)),
                     Task('tasks.data.relative.sample_tasks.multiply', args=(2,))):
            try:
                task.materialize()
                raise Exception('Should raise.')
            except RuntimeError as exc:
                assert 'must have a .run() method' in str(exc)

    def test_callable_to_runnable_tgt(self):  # pylint: disable=R0201
        """TODO."""
        import sys
        task = Task(callable_to_runnable)
        materialized_task_result(task, sys.maxsize)

        task = Task(callable_to_runnable_with_arg, args=(2,))
        materialized_task_result(task, 2)

        from .data import sample_tasks
        task = Task(sample_tasks.callable_to_runnable, args=(2,))
        materialized_task_result(task, 4)

        task = Task(sample_tasks.callable_to_adapted_runnable, args=(2,))
        materialized_task_result(task, 4)

    def test_string_callable_to_runnable_tgt(self):  # pylint: disable=R0201
        """TODO."""
        import sys
        task = Task('callable_to_runnable', module=__name__)
        materialized_task_result(task, sys.maxsize)

        task = Task('callable_to_runnable_with_arg',
                    module=__name__, args=(2,))
        materialized_task_result(task, 2)

        task = Task('tasks.data.sample_tasks.callable_to_runnable', args=(2,))
        materialized_task_result(task, 4)

        task = Task('tasks.data.sample_tasks.callable_to_adapted_runnable',
                    args=(2,))
        materialized_task_result(task, 4)

    def test_path_usage(self):  # pylint: disable=R0201
        """TODO."""
        dirname = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dirname, 'data', 'relative')

        task = Task('sample_tasks.Multiplier', args=(4,), path=path)
        materialized_task_result(task, 8)

        task = Task('Multiplier', module='sample_tasks', args=(4,), path=path)
        materialized_task_result(task, 8)

        task = Task('sample_tasks.callable_to_runnable',
                    args=(2,), path=path)
        materialized_task_result(task, 4)

        task = Task('callable_to_runnable',
                    args=(2,), module='sample_tasks', path=path)
        materialized_task_result(task, 4)


# pylint: disable=R0201
class TestTaskSerialization(object):
    """TODO."""

    def test_serialize(self):
        """TODO."""
        import sys
        task = Task('Runnable', module=__name__)
        materialized_task_result(task, sys.maxsize, serialize=True)

        task = Task('RunnableWithArg', module=__name__, args=(2,))
        materialized_task_result(task, 2, serialize=True)

        task = Task('RunnableWithArg', module=__name__, kwargs={'number': 3})
        materialized_task_result(task, 3, serialize=True)

        dirname = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dirname, 'data', 'relative')
        task = Task('Multiplier', module='sample_tasks', args=(4,), path=path)
        materialized_task_result(task, 8, serialize=True)

    def test_raise_on_serialization(self):
        """TODO."""
        try:
            task = Task(RunnableTaskAdaptor(lambda x: x * 2, 3))
            materialized_task_result(task, 6, serialize=True)
            raise Exception('Should raise.')
        except TaskSerializationError:
            pass

    def test_raise_on_deserialization(self):
        """TODO."""
        # To add a case of a serializable but not
        # deserializable task.

        try:
            Task().loads(None)
            raise Exception('Should raise.')
        except TaskDeserializationError:
            pass
