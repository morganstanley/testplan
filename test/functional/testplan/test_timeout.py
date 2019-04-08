import os
import time

from testplan import Testplan
from testplan.runnable import TestRunner
from testplan.runners.base import Executor
from testplan.runners.pools import ThreadPool, ProcessPool
from testplan.runners.pools.tasks import Task
from testplan.report.testing import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER

from test.functional.testplan import func_basic_tasks


class MyTestRunner(TestRunner):
    """Customized TestRunner"""
    def _wait_ongoing(self):
        """
        Time sensitive testcase should not depend on system time, operating
        system might be busy scheduling processes with CPU and IO resources,
        sometimes the Multitest tasks (especially executed in pool) cannot be
        finished within specified time, testcase would be unstable. So just
        make some tasks which would take long time to execute, and in a mocked
        TestRunner we can detect these tasks remaining in executors, then we
        can start timeout event handling.
        """
        if self.resources.start_exceptions:
            for resource, exception in self.resources.start_exceptions.items():
                self.logger.critical(
                    'Aborting {} due to start exception:'.format(resource))
                self.logger.error(exception)
                resource.abort()

        while self.active:
            pending_work = False
            timeout_flag = True

            for resource in self.resources:
                if isinstance(resource, Executor):
                    # Poll the resource's health to avoid hanging.
                    if not resource.is_alive:
                        self.result.test_report.logger.critical(
                            'Aborting {} - {} unexpectedly died'.format(
                                self, resource))
                        self.abort()
                        self.result.test_report.status_override = Status.ERROR
                    if len(resource.ongoing) > 0:
                        pending_work = True
                    # For each executor, there will be 2 tasks added, one is
                    # light weight and the other takes long time to run. When
                    # there is only one task remaining in each executor it is
                    # indicated that a timeout event should occur.
                    if self.cfg.timeout and len(resource.ongoing) > 1:
                        timeout_flag = False

            if not pending_work:
                # Should not happen, timeout event should occur before all tasks
                # finished, or there is something wrong and this test fails.
                break

            if self.cfg.timeout and (timeout_flag or time.time() >
                    self._start_time + min(self.cfg.timeout, 600)):
                self.result.test_report.logger.error(
                    'Timeout: Aborting execution after {} seconds'.format(
                        self.cfg.timeout))
                for dep in self.abort_dependencies():
                    self._abort_entity(dep)
                time.sleep(self.cfg.abort_wait_timeout)
                break

            time.sleep(self.cfg.active_loop_sleep)


def test_runner_timeout():
    """
    Execute MultiTests in LocalRunner, ThreadPool and ProcessPool respectively.
    Some of them will timeout and we'll get a report showing execution details.
    """
    plan = Testplan(name='plan', parse_cmdline=False,
                    runnable=MyTestRunner,
                    timeout=60, abort_wait_timeout=5)
    mod_path = os.path.dirname(os.path.abspath(__file__))

    THREAD_POOL = 'MyThreadPool'
    PROCESS_POOL = 'MyProcessPool'
    thread_pool = ThreadPool(name=THREAD_POOL, size=2, worker_heartbeat=None)
    proc_pool = ProcessPool(name=PROCESS_POOL, size=2, worker_heartbeat=None)
    plan.add_resource(thread_pool)
    plan.add_resource(proc_pool)
    plan.add(func_basic_tasks.get_mtest1())
    plan.add(func_basic_tasks.get_mtest2())

    task3 = Task(target='get_mtest3', module='func_basic_tasks', path=mod_path)
    task4 = Task(target='get_mtest4', module='func_basic_tasks', path=mod_path)
    task5 = Task(target='get_mtest5', module='func_basic_tasks', path=mod_path)
    task6 = Task(target='get_mtest6', module='func_basic_tasks', path=mod_path)
    plan.schedule(task3, resource=THREAD_POOL)
    plan.schedule(task4, resource=THREAD_POOL)
    plan.schedule(task5, resource=PROCESS_POOL)
    plan.schedule(task6, resource=PROCESS_POOL)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 6
    assert plan.report.status == Status.ERROR

    entries = plan.report.entries
    assert entries[0].name == 'MTest1'
    assert entries[0].status == Status.FAILED  # testcase 'test_true' failed
    assert entries[2].name == 'MTest3'
    assert entries[2].status == Status.PASSED  # testcase 'test_equal' passed
    assert entries[4].name == 'MTest5'
    assert entries[4].status == Status.ERROR   # testcase 'test_contain' raised
    assert entries[1].name == 'MTest2'
    assert entries[1].status == Status.ERROR   # timeout
    assert ' discarding due to ' in entries[1].logs[0]['message']
    assert entries[3].name == 'Task[get_mtest4]'
    assert entries[3].status == Status.ERROR   # timeout
    assert entries[3].logs[0]['message'].startswith('_target: get_mtest4')
    assert ' discarding due to ' in entries[3].logs[1]['message']
    assert entries[5].name == 'Task[get_mtest6]'
    assert entries[5].status == Status.ERROR   # timeout
    assert entries[5].logs[0]['message'].startswith('_target: get_mtest6')
    assert ' discarding due to ' in entries[5].logs[1]['message']
