"""Discoverable task targets that will be instantiated to task objects"""
from testplan.runners.pools.tasks.base import task_target
from testplan.testing.multitest import MultiTest
from sub_proj2.suites import Suite1, Suite2


@task_target
def make_multitest1(stop_on_error=True):
    # a test target only returns 1 runnable object
    test = MultiTest(
        name="Proj2-Suite1", suites=[Suite1()], stop_on_error=stop_on_error
    )
    return test


@task_target
def make_multitest2(stop_on_error=True):
    # a test target only returns 1 runnable object
    test = MultiTest(
        name="Proj2-Suite2", suites=[Suite2()], stop_on_error=stop_on_error
    )
    return test
