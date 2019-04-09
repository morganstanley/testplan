"""Unit test for process pool."""
import psutil
import pytest
import time
import threading

from testplan.runners.pools import process
from testplan.runners.pools import tasks
from testplan.common.utils import logger

from tests.unit.testplan.runners.pools.tasks.data.sample_tasks import Runnable

logger.TESTPLAN_LOGGER.setLevel(logger.DEBUG)


@pytest.fixture
def proc_pool():
    return process.ProcessPool(name='ProcPool', size=2)


class TestProcPool(object):
    """Tests for the ProcessPool class."""

    def test_run_task(self, proc_pool):
        """
        Test that a simple Task can be scheduled to a process pool and run.
        """
        # Create and add a basic example Task. When materialized and run,
        # the Runnable will return the product of its args: 7 * 3 => 21.
        example_task = tasks.Task(target=Runnable, args=(7, 3))
        proc_pool.add(example_task, example_task.uid())
        with proc_pool:
            assert proc_pool.status.tag == proc_pool.status.STARTED
            while proc_pool.pending_work():
                assert proc_pool.is_alive
                time.sleep(0.2)

        assert proc_pool.status.tag == proc_pool.status.STOPPED

        # Check that the expected result is stored both on the worker and
        # on the pool's result.
        assert proc_pool.get(example_task.uid()).result == 21
        assert proc_pool.results[example_task.uid()].result == 21

    def test_add_main(self, proc_pool):
        """
        Test scheduling a Task from the __main__ module. This should not be
        allowed, since __main__ is a different module for the child process.
        """
        main_task = tasks.Task(target='runnable', module='__main__')
        with pytest.raises(ValueError):
            proc_pool.add(main_task, main_task.uid())

    def test_process_cleanup(self, proc_pool):
        current_proc = psutil.Process()
        start_children = current_proc.children()
        start_thread_count = threading.active_count()

        proc_pool.start()
        print('Pool started')
        assert len(current_proc.children()) == len(start_children) + 2
        print('Now have {} new threads.'.format(threading.active_count() - start_thread_count))

        proc_pool.stop()
        print('Pool stopped')
        assert len(current_proc.children()) == len(start_children)
        assert threading.active_count() == start_thread_count

    def test_repeated_start_stop(self, proc_pool):
        for i in range(10):
            print('\nIteration {}'.format(i))

            print('Starting proc_pool...')
            proc_pool.start()
            proc_pool.wait(proc_pool.status.STARTED)
            print('proc_pool started.')

            print('Stopping proc_pool...')
            proc_pool.stop()
            proc_pool.wait(proc_pool.status.STOPPED)
            print('proc_pool stopped.')

