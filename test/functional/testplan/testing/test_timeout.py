import os

from testplan import Testplan
from testplan.runners.pools import ThreadPool, ProcessPool
from testplan.runners.pools.tasks import Task
from testplan.report.testing import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER

from test.functional.testplan.testing import func_basic_tasks


def test_runner_timeout():
    """
    Execute MultiTests in LocalRunner, ThreadPool and ProcessPool respectively.
    Some of them will timeout and we'll get a report showing execution details.
    """
    plan = Testplan(name='plan', parse_cmdline=False,
                    timeout=10, abort_wait_timeout=5)
    thread_pool_name = 'MyThreadPool'
    proc_pool_name = 'MyProcessPool'
    mod_path = os.path.dirname(os.path.abspath(__file__))

    pool1 = ThreadPool(name=thread_pool_name, size=2)
    pool2 = ProcessPool(name=proc_pool_name, size=2)
    plan.add_resource(pool1)
    plan.add_resource(pool2)
    plan.add(func_basic_tasks.get_mtest1())
    plan.add(func_basic_tasks.get_mtest2())

    task3 = Task(target='get_mtest3', module='func_basic_tasks', path=mod_path)
    task4 = Task(target='get_mtest4', module='func_basic_tasks', path=mod_path)
    task5 = Task(target='get_mtest5', module='func_basic_tasks', path=mod_path)
    task6 = Task(target='get_mtest6', module='func_basic_tasks', path=mod_path)
    plan.schedule(task3, resource=thread_pool_name)
    plan.schedule(task4, resource=thread_pool_name)
    plan.schedule(task5, resource=proc_pool_name)
    plan.schedule(task6, resource=proc_pool_name)

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
