import os

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.runners.pools import ThreadPool
from testplan.runners.pools.tasks import Task
from testplan.report.testing import Status
from testplan.common.utils.testing import log_propagation_disabled
from testplan.logger import TESTPLAN_LOGGER


@testsuite
class Suite1(object):
    """A test suite with parameterized testcases."""
    @testcase(
        parameters=tuple(range(10))
    )
    def test_true(self, env, result, val):
        result.true(val, description='Check if value is true')


@testsuite
class Suite2(object):
    """A test suite with parameterized testcases."""
    @testcase(
        parameters=(
            False,
            True,
            None,
        )
    )
    def test_false(self, env, result, val):
        result.false(val, description='Check if value is false')


def get_mtest(part_tuple=None):
    test = MultiTest(name='MTest',
                     suites=[Suite1(), Suite2()],
                     part=part_tuple)
    return test


def test_multi_parts_not_merged():
    """Execute MultiTest parts but do not merge report."""
    plan = Testplan(name='plan', parse_cmdline=False,
                    merge_scheduled_parts=False)
    pool = ThreadPool(name='MyPool', size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource='MyPool')

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    assert len(plan.report.entries) == 3
    assert plan.report.entries[0].name == 'MTest - part(1/3)'
    assert plan.report.entries[1].name == 'MTest - part(2/3)'
    assert plan.report.entries[2].name == 'MTest - part(3/3)'
    assert len(plan.report.entries[0].entries) == 2  # 2 suites
    assert plan.report.entries[0].entries[0].name == 'Suite1'
    assert plan.report.entries[0].entries[1].name == 'Suite2'
    assert len(plan.report.entries[0].entries[0].entries) == 1  # param group
    assert plan.report.entries[0].entries[0].entries[0].name == 'test_true'
    assert len(plan.report.entries[0].entries[1].entries) == 1  # param group
    assert plan.report.entries[0].entries[1].entries[0].name == 'test_false'
    assert len(plan.report.entries[0].entries[0].entries[0].entries) == 4
    assert len(plan.report.entries[0].entries[1].entries[0].entries) == 1


def test_multi_parts_merged():
    """Execute MultiTest parts and merge report."""
    plan = Testplan(name='plan', parse_cmdline=False,
                    merge_scheduled_parts=True)
    pool = ThreadPool(name='MyPool', size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource='MyPool')

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    assert len(plan.report.entries) == 1
    assert plan.report.entries[0].name == 'MTest'
    assert len(plan.report.entries[0].entries) == 2  # 2 suites
    assert plan.report.entries[0].entries[0].name == 'Suite1'
    assert plan.report.entries[0].entries[1].name == 'Suite2'
    assert len(plan.report.entries[0].entries[0].entries) == 1  # param group
    assert plan.report.entries[0].entries[0].entries[0].name == 'test_true'
    assert len(plan.report.entries[0].entries[1].entries) == 1  # param group
    assert plan.report.entries[0].entries[1].entries[0].name == 'test_false'
    assert len(plan.report.entries[0].entries[0].entries[0].entries) == 10
    assert len(plan.report.entries[0].entries[1].entries[0].entries) == 3


def test_multi_parts_invalid_parameter_1():
    """
    Execute MultiTest parts with invalid parameters that a part of
    MultiTest has been scheduled twice.
    """
    plan = Testplan(name='plan', parse_cmdline=False,
                    merge_scheduled_parts=True)
    pool = ThreadPool(name='MyPool', size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource='MyPool')
    plan.schedule(Task(target=get_mtest(part_tuple=(1, 3))),
                  resource='MyPool')

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.FAILED  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.FAILED  # Suite2
    assert 'invalid parameter of part provided' in \
           plan.report.entries[0].logs[0]['message']


def test_multi_parts_invalid_parameter_2():
    """
    Execute MultiTest parts with invalid parameters that a MultiTest
    has been scheduled twice.
    """
    plan = Testplan(name='plan', parse_cmdline=False,
                    merge_scheduled_parts=True)
    pool = ThreadPool(name='MyPool', size=2)
    plan.add_resource(pool)

    for idx in range(3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource='MyPool')
    for idx in range(2):
        task = Task(target=get_mtest(part_tuple=(idx, 2)))
        plan.schedule(task, resource='MyPool')

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.FAILED  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.FAILED  # Suite2
    assert 'invalid parameter of part provided' in \
           plan.report.entries[0].logs[0]['message']


def test_multi_parts_missing_parts():
    """
    Execute MultiTest parts with invalid parameters that not all
    parts of a MultiTest has been scheduled.
    """
    plan = Testplan(name='plan', parse_cmdline=False,
                    merge_scheduled_parts=True)
    pool = ThreadPool(name='MyPool', size=2)
    plan.add_resource(pool)

    for idx in range(1, 3):
        task = Task(target=get_mtest(part_tuple=(idx, 3)))
        plan.schedule(task, resource='MyPool')

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is False

    assert len(plan.report.entries) == 1
    assert len(plan.report.entries[0].entries) == 2
    assert plan.report.status == Status.ERROR  # Testplan result
    assert plan.report.entries[0].status == Status.ERROR  # Multitest
    assert plan.report.entries[0].entries[0].status == Status.PASSED  # Suite1
    assert plan.report.entries[0].entries[1].status == Status.FAILED  # Suite2
    assert 'not all MultiTest parts had been scheduled' in \
           plan.report.entries[0].logs[0]['message']
