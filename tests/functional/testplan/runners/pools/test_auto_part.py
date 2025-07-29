import os
import math
import tempfile
from itertools import count
from pathlib import Path

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
                    "teardown_time": 0,
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
        mockplan.run()
        assert pool.size == 2


def test_auto_parts_discover_interactive(runpath):
    mockplan = TestplanMock(
        "plan",
        runpath=runpath,
        merge_scheduled_parts=True,
        auto_part_runtime_limit=45,
        plan_runtime_target=200,
        interactive_port=0,
        runtime_data={
            "Proj1-suite": {
                "execution_time": 199.99,
                "setup_time": 5,
                "teardown_time": 0,
            }
        },
    )
    pool = ProcessPool(name="MyPool", size="auto")
    mockplan.add_resource(pool)
    current_folder = Path(__file__).resolve().parent
    mockplan.schedule_all(
        path=current_folder / "discover_tasks",
        name_pattern=r".*auto_parts_tasks\.py$",
        resource="MyPool",
    )

    local_pool = mockplan.resources.get(mockplan.resources.first())
    # validate that only one task added to the local pool without split

    assert len(pool.added_items) == 0
    assert len(local_pool.added_items) == 1


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
                    "teardown_time": 0,
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
        mockplan.run()
        assert pool.size == 1


def test_auto_parts_zero_neg_parts():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=45,
            plan_runtime_target=200,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 50,
                    "setup_time": 50,  # setup_time > runtime_limit -> negtive num_of_parts
                    "teardown_time": 0,
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
        assert len(pool.added_items) == 1
        for task in pool.added_items.values():
            assert task.weight == 100
        mockplan.run()
        assert pool.size == 1


def test_auto_parts_cap_parts():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=45,
            plan_runtime_target=200,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 60,
                    "setup_time": 44,
                    "teardown_time": 0,
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
        assert len(pool.added_items) == 3
        for task in pool.added_items.values():
            assert task.weight == 64
        mockplan.run()
        assert pool.size == 1


def test_auto_parts_discover_with_teardown_time():
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
                    "setup_time": 2.5,
                    "teardown_time": 2.5,
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
        mockplan.run()
        assert pool.size == 2


def test_auto_parts_discover_interactive_with_teardown_time(runpath):
    mockplan = TestplanMock(
        "plan",
        runpath=runpath,
        merge_scheduled_parts=True,
        auto_part_runtime_limit=45,
        plan_runtime_target=200,
        interactive_port=0,
        runtime_data={
            "Proj1-suite": {
                "execution_time": 199.99,
                "setup_time": 5,
                "teardown_time": 5,
            }
        },
    )
    pool = ProcessPool(name="MyPool", size="auto")
    mockplan.add_resource(pool)
    current_folder = Path(__file__).resolve().parent
    mockplan.schedule_all(
        path=current_folder / "discover_tasks",
        name_pattern=r".*auto_parts_tasks\.py$",
        resource="MyPool",
    )

    local_pool = mockplan.resources.get(mockplan.resources.first())
    # validate that only one task added to the local pool without split

    assert len(pool.added_items) == 0
    assert len(local_pool.added_items) == 1


def test_auto_weight_discover_with_teardown_time():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            plan_runtime_target=300,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 199.99,
                    "setup_time": 19.99,
                    "teardown_time": 19.99,
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
        mockplan.run()
        assert pool.size == 1


def test_auto_parts_zero_neg_parts_with_teardown_time():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=45,
            plan_runtime_target=200,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 50,
                    "setup_time": 25,  # setup_time + teardown_time > runtime_limit -> negtive num_of_parts
                    "teardown_time": 25,
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
        assert len(pool.added_items) == 1
        for task in pool.added_items.values():
            assert task.weight == 100
        mockplan.run()
        assert pool.size == 1


def test_auto_parts_cap_parts_with_teardown_time():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=45,
            plan_runtime_target=200,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 60,
                    "setup_time": 22,
                    "teardown_time": 22,
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
        assert len(pool.added_items) == 3
        for task in pool.added_items.values():
            assert task.weight == 64
        mockplan.run()
        assert pool.size == 1


def test_auto_part_runtime_limit():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit="auto",
            plan_runtime_target=2400,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 3600,
                    "setup_time": 300,
                    "teardown_time": 0,
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
        assert len(pool.added_items) == 6
        for task in pool.added_items.values():
            assert task.weight == 900
        mockplan.run()
        assert pool.size == 3


def test_auto_plan_runtime_target():
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit="auto",
            plan_runtime_target="auto",
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 3600,
                    "setup_time": 300,
                    "teardown_time": 0,
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
        assert len(pool.added_items) == 6
        for task in pool.added_items.values():
            assert task.weight == 900
        mockplan.run()
        assert pool.size == 6


@pytest.mark.parametrize(
    "tc, adjusted_exec_t, exp_weight, exp_parts",
    [
        (10, 60, 35, 2),
        (5, 120, 35, 4),
        (20, 30, 35, 1),
        (8, 75, 30, 3),
        (100, 15, 20, 1),
    ],
    ids=count(0),
)
def test_multitest_weight_adjusted_by_relative_testcase_count(
    tc, adjusted_exec_t, exp_weight, exp_parts
):
    with tempfile.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan",
            runpath=runpath,
            merge_scheduled_parts=True,
            auto_part_runtime_limit=40,
            plan_runtime_target=80,
            runtime_data={
                "Proj1-suite": {
                    "execution_time": 60,
                    "setup_time": 5,
                    "teardown_time": 0,
                    "testcase_count": tc,
                }
            },
        )
        pool = ProcessPool(name="MyPool", size="auto")
        mockplan.add_resource(pool)
        current_folder = Path(__file__).resolve().parent
        assert pool.cfg.runtime_data == {
            "Proj1-suite": {
                "execution_time": 60,
                "setup_time": 5,
                "teardown_time": 0,
                "testcase_count": tc,
            }
        }
        # curr tc: 10
        mockplan.schedule_all(
            path=current_folder / "discover_tasks",
            name_pattern=r".*auto_parts_tasks\.py$",
            resource="MyPool",
        )
        assert pool.cfg.runtime_data == {
            "Proj1-suite": {
                "execution_time": adjusted_exec_t,
                "setup_time": 5,
                "teardown_time": 0,
                "testcase_count": 10,
            }
        }
        assert len(pool.added_items) == exp_parts
        for task in pool.added_items.values():
            assert task.weight == exp_weight
        mockplan.run()
        assert pool.size == math.ceil(exp_weight * exp_parts / 80)
