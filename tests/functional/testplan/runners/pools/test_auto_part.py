import os
import tempfile

import pytest

from testplan import TestplanMock
from testplan.runners.pools.tasks.base import Task
from testplan.runners.pools.process import ProcessPool


def test_auto_parts_discover():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=45,
            plan_runtime_target=200,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 199.99,
                    "setup_time": 5,
                }
            },
        )
        pool = ProcessPool(name="MyPool", size="auto")
        mockplan.add_resource(pool)
        current_folder = os.path.dirname(os.path.realpath(__file__))
        mockplan.schedule_all(
            path=f"{current_folder}/discover_tasks",
            name_pattern=r".*auto_parts_tasks\.py$",
            resource="MyPool",
        )
        assert len(pool.added_items) == 5
        for task in pool.added_items.values():
            assert task.weight == 45

        assert pool.size == 2


def test_auto_weight_discover():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            plan_runtime_target=300,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 199.99,
                    "setup_time": 39.99,
                }
            },
        )
        pool = ProcessPool(name="MyPool", size="auto")
        mockplan.add_resource(pool)
        current_folder = os.path.dirname(os.path.realpath(__file__))
        mockplan.schedule_all(
            path=f"{current_folder}/discover_tasks",
            name_pattern=r".*auto_weight_tasks\.py$",
            resource="MyPool",
        )
        assert len(pool.added_items) == 2
        for task in pool.added_items.values():
            assert task.weight == 140

        assert pool.size == 1
