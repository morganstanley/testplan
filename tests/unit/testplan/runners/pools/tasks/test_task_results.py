from testplan.runners.pools.tasks import Task, TaskResult


class TestTaskResultInitialization:
    """TODO."""

    def test_basic_init(self):
        """TODO."""
        task = Task("Runnable", module=__name__)
        result = "result"
        for task_result in (
            TaskResult(task, result, True, None, None),
            TaskResult(task, result, True, "msg", None),
            TaskResult(
                task, result, True, None, [Task("Runnable", module=__name__)]
            ),
        ):
            serialized = task_result.dumps()
            new_task_result = TaskResult().loads(serialized)

            for attr in ("result", "status", "_reason", "_uid"):
                task_result_attr = getattr(task_result, attr)
                new_task_result_attr = getattr(new_task_result, attr)
                assert task_result_attr == new_task_result_attr

            assert task_result._task._uid == new_task_result._task._uid
            if task_result.follow is None:
                assert task_result.follow == new_task_result.follow
            else:
                assert len(task_result.follow) == len(new_task_result.follow)
                for idx, task in enumerate(task_result.follow):
                    assert task._uid == new_task_result.follow[idx]._uid
