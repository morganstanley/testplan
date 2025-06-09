"""Unit test for process pool."""

import platform
import psutil
import pytest
import time

from testplan.runners.pools import process
from testplan.runners.pools import tasks
from testplan.common.utils import logger
from testplan.testing.common import SkipStrategy

logger.TESTPLAN_LOGGER.setLevel(logger.DEBUG)


@pytest.fixture
def proc_pool():
    pool = process.ProcessPool(
        name="ProcPool", size=2, restart_count=0, async_start=False
    )
    pool.cfg.set_local("skip_strategy", SkipStrategy.noop())
    return pool


class TestProcPool:
    """Tests for the ProcessPool class."""

    def test_run_task(self, proc_pool):
        """
        Test that a simple Task can be scheduled to a process pool and run.
        """
        # Create and add a basic example Task. When materialized and run,
        # the Runnable will return the product of its args: 7 * 3 => 21.
        example_task = tasks.Task(
            target="Runnable",
            module="tests.unit.testplan.runners.pools.tasks.data.sample_tasks",
            args=(7, 3),
        )
        proc_pool.add(example_task, example_task.uid())
        with proc_pool:
            assert proc_pool.status == proc_pool.status.STARTED
            while proc_pool.pending_work():
                assert proc_pool.is_alive
                time.sleep(0.2)

        assert proc_pool.status == proc_pool.status.STOPPED

        # Check that the expected result is stored both on the worker and
        # on the pool's result.
        assert proc_pool.get(example_task.uid()).result.report.val == 21
        assert proc_pool.results[example_task.uid()].result.report.val == 21

    def test_add_main(self, proc_pool):
        """
        Test scheduling a Task from the __main__ module. This should not be
        allowed, since __main__ is a different module for the child process.
        """
        main_task = tasks.Task(target="runnable", module="__main__")
        with pytest.raises(ValueError):
            proc_pool.add(main_task, main_task.uid())

    def test_start_stop(self, proc_pool):
        """Test basic start/stop of ProcessPool."""
        # This testcase is known to fail on Windows - mark as xfail until we
        # can fix it up.
        if platform.system() == "Windows":
            pytest.xfail("ProcPool start/stop is unstable on Windows")

        current_proc = psutil.Process()
        start_children = current_proc.children()

        # Iterate 5 times to increase the chance of hitting a race condition.
        for _ in range(5):
            with proc_pool:
                assert proc_pool.status == proc_pool.status.STARTED
                assert len(current_proc.children()) == len(start_children) + 2

            assert proc_pool.status == proc_pool.status.STOPPED
            assert len(current_proc.children()) == len(start_children)
