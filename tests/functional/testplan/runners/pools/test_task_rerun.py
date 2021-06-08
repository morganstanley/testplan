"""
Task rerun feature functional tests.

The task with `rerun` attribute set can be re-assign to pool if fails,
re-assign count cannot exceed the value of `rerun`, all of the results
should be saved.
"""

import os
import tempfile
import getpass
import uuid

from testplan import Task, TestplanMock
from testplan.common.utils import path
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.base import Driver, DriverConfig
from testplan.runners.pools import ThreadPool, ProcessPool
from testplan.common.config import ConfigOption as Optional
from testplan.common.utils.path import makedirs
from testplan.report import ReportCategories


class MockDriverConfig(DriverConfig):
    @classmethod
    def get_options(cls):
        return {
            Optional("start_raises", default=False): bool,
            Optional("stop_raises", default=False): bool,
        }


class MockDriver(Driver):
    """
    A mock driver used to check that the environment is correctly
    started and stopped.
    """

    CONFIG = MockDriverConfig

    def __init__(self, start_raises=False, stop_raises=False, **options):
        options.update(self.filter_locals(locals()))
        super(MockDriver, self).__init__(**options)
        self._start_done = False
        self._stop_done = False
        self._start_raises = start_raises
        self._stop_raises = stop_raises

    def starting(self):
        super(MockDriver, self).starting()
        if self._start_raises:
            raise RuntimeError("MockDriver fails to start")
        self._start_done = True

    def stopping(self):
        super(MockDriver, self).stopping()
        if self._stop_raises:
            raise RuntimeError("MockDriver fails to stop")
        self._stop_done = True


class UnstableSuiteBase(object):
    """
    In this test suite a temporary file is created
    to record how many times does it run.
    """

    def __init__(self, tmp_file, max_retries):
        self._iteration = -1
        self._max_retries = max_retries
        self._tmp_file = tmp_file

    def setup(self, env, result):
        makedirs(os.path.dirname(self._tmp_file))
        if not os.path.exists(self._tmp_file):
            self._iteration = 0
        else:
            with open(self._tmp_file, "r") as fp:
                try:
                    self._iteration = int(fp.read())
                except Exception:
                    self._iteration = 0

        if self._iteration == self._max_retries:  # iter starts from zero
            os.remove(self._tmp_file)
        else:
            with open(self._tmp_file, "w") as fp:
                fp.write(str(self._iteration + 1))

        result.log("Suite setup in iteration {}".format(self._iteration))


@testsuite
class UnstableSuite1(UnstableSuiteBase):
    @testcase
    def unstable_case(self, env, result):
        if self._iteration == 0:
            result.fail("Testcase fails in this iteration")
        else:
            result.log("Testcase passes in this iteration")

    @testcase
    def unstable_driver(self, env, result):
        if self._iteration == 1:
            env.mock_driver._stop_raises = True
        else:
            result.log("MockDriver does not raise in this iteration")


@testsuite
class UnstableSuite2(UnstableSuiteBase):
    @testcase
    def unstable_worker(self, env, result):
        if self._iteration == 0:
            result.log("Kill the runner")
            os._exit(1)
        result.log("Do not kill the runner in this iteration")


@testsuite
class UnstableSuite3(UnstableSuiteBase):
    @testcase
    def unstable_case(self, env, result):
        if self._iteration > 2:
            result.log("Testcase passes after retry 3 times")
        else:
            result.fail("Testcase fails in this iteration")


@testsuite
class SuiteForParts:
    @testcase
    def case_0(self, env, result):
        result.fail("this case fails")

    @testcase
    def case_1(self, env, result):
        result.log("this case passes")

    @testcase
    def case_2(self, env, result):
        result.log("this case passes")


def make_multitest_1(tmp_file):
    return MultiTest(
        name="Unstable MTest1",
        description="MultiTest that fails in iteration 0 & 1, and passes on 2",
        suites=[UnstableSuite1(tmp_file=tmp_file, max_retries=2)],
        environment=[MockDriver(name="mock_driver")],
    )


def make_multitest_2(tmp_file):
    return MultiTest(
        name="Unstable MTest2",
        description="MultiTest that fails in iteration 0, and passes on 1",
        suites=[UnstableSuite2(tmp_file=tmp_file, max_retries=1)],
        environment=[],
    )


def make_multitest_3(tmp_file):
    return MultiTest(
        name="Unstable MTest3",
        description="MultiTest that passes until iteration 4",
        suites=[UnstableSuite3(tmp_file=tmp_file, max_retries=4)],
        environment=[],
    )


def make_multitest_parts(part_tuple):
    return MultiTest(
        name="MultiTestParts",
        suites=[SuiteForParts()],
        part=part_tuple,
    )


def _remove_existing_tmp_file(tmp_file):
    """Make sure the temporary file is removed."""
    if os.path.isfile(tmp_file):
        os.remove(tmp_file)


def test_task_rerun_in_thread_pool(mockplan):
    """
    Test procedure:
      - 1st run: `unstable_case` fails.
      - 1st rerun: `mock_driver` raises during stop.
      - 2nd rerun: all pass.
    """
    pool_name = ThreadPool.__name__
    pool = ThreadPool(name=pool_name, size=2)
    mockplan.add_resource(pool)

    directory = os.path.dirname(os.path.abspath(__file__))
    tmp_file = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    task = Task(
        target=make_multitest_1, path=directory, args=(tmp_file,), rerun=3
    )
    uid = mockplan.schedule(task=task, resource=pool_name)

    assert mockplan.run().run is True
    assert mockplan.report.passed is True
    assert mockplan.report.counter == {"passed": 3, "total": 3, "failed": 0}

    assert isinstance(mockplan.report.serialize(), dict)
    assert mockplan.result.test_results[uid].report.name == "Unstable MTest1"
    assert len(mockplan.report.entries) == 3
    assert mockplan.report.entries[-1].category == ReportCategories.TASK_RERUN
    assert mockplan.report.entries[-2].category == ReportCategories.TASK_RERUN

    assert task.reassign_cnt == 2
    _remove_existing_tmp_file(tmp_file)


def test_task_rerun_in_process_pool(mockplan):
    """
    Test 1 procedure:
      - 1st run: `unstable_case` fails.
      - 1st rerun: `mock_driver` raises during stop.
      - 2nd rerun: all pass.
    Test 2 procedure:
      - 1st run: `unstable_worker` makes child process exit.
      - monitor detects inactive worker, decommission the task from worker,
        then re-assign it and it passes (no rerun is needed).
    """
    pool_name = ProcessPool.__name__
    pool = ProcessPool(name=pool_name, size=2)
    mockplan.add_resource(pool)

    directory = os.path.dirname(os.path.abspath(__file__))
    tmp_file_1 = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    tmp_file_2 = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    task1 = Task(
        target=make_multitest_1, path=directory, args=(tmp_file_1,), rerun=2
    )
    task2 = Task(
        target=make_multitest_2, path=directory, args=(tmp_file_2,), rerun=0
    )
    uid1 = mockplan.schedule(task=task1, resource=pool_name)
    uid2 = mockplan.schedule(task=task2, resource=pool_name)

    assert mockplan.run().run is True
    assert mockplan.report.passed is True
    assert mockplan.report.counter == {"passed": 5, "total": 5, "failed": 0}

    assert isinstance(mockplan.report.serialize(), dict)
    assert mockplan.result.test_results[uid1].report.name == "Unstable MTest1"
    assert mockplan.result.test_results[uid2].report.name == "Unstable MTest2"
    assert len(mockplan.report.entries) == 4
    assert mockplan.report.entries[-1].category == ReportCategories.TASK_RERUN
    assert mockplan.report.entries[-2].category == ReportCategories.TASK_RERUN

    assert task1.reassign_cnt == 2
    assert task2.reassign_cnt == 0  # 1st run: assigned but not executed
    assert pool._task_retries_cnt[uid2] == 1
    _remove_existing_tmp_file(tmp_file_1)
    _remove_existing_tmp_file(tmp_file_2)


def test_task_rerun_with_more_times(mockplan):
    """
    Test procedure 1:
      (set `task_rerun_limit` to 2, a task can be scheduled 3 times in total)
      - 1st run: `unstable_case` fails.
      - 1st rerun: `unstable_case` fails.
      - 2nd rerun: `unstable_case` fails.
    """
    pool_name = ThreadPool.__name__
    pool = ThreadPool(name=pool_name, size=1)
    mockplan.add_resource(pool)

    directory = os.path.dirname(os.path.abspath(__file__))
    tmp_file = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    task = Task(
        target=make_multitest_3, path=directory, args=(tmp_file,), rerun=2
    )
    uid = mockplan.schedule(task=task, resource=pool_name)

    assert mockplan.run().run is True
    assert mockplan.report.passed is False
    assert mockplan.report.counter == {"passed": 1, "total": 2, "failed": 1}
    assert mockplan.result.test_results[uid].report.name == "Unstable MTest3"

    assert task.reassign_cnt == 2
    # test fails, should manually remove it
    _remove_existing_tmp_file(tmp_file)


def test_task_rerun_with_more_times_2(mockplan):
    """
    Test procedure 2:
      (set `task_rerun_limit` to 4, a task can be scheduled 5 times in total)
      - 1st run: `unstable_case` fails.
      - 1st rerun: `unstable_case` fails.
      - 2nd rerun: `unstable_case` fails.
      - 3rd rerun: all pass.
    """
    pool_name = ThreadPool.__name__
    pool = ThreadPool(name=pool_name, size=1)
    mockplan.add_resource(pool)

    directory = os.path.dirname(os.path.abspath(__file__))
    tmp_file = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    task = Task(
        target=make_multitest_3, path=directory, args=(tmp_file,), rerun=3
    )
    uid = mockplan.schedule(task=task, resource=pool_name)

    assert mockplan.run().run is True
    assert mockplan.report.passed is True
    assert mockplan.report.counter == {"passed": 2, "total": 2, "failed": 0}
    assert mockplan.result.test_results[uid].report.name == "Unstable MTest3"

    assert task.reassign_cnt == 3
    _remove_existing_tmp_file(tmp_file)


def test_task_rerun_with_parts():

    with path.TemporaryDirectory() as runpath:
        mockplan = TestplanMock(
            "plan", runpath=runpath, merge_scheduled_parts=True
        )

        pool_name = ThreadPool.__name__
        pool = ThreadPool(name=pool_name, size=1)
        mockplan.add_resource(pool)

        directory = os.path.dirname(os.path.abspath(__file__))

        uids = []
        for idx in range(3):
            task = Task(
                target=make_multitest_parts,
                path=directory,
                kwargs={"part_tuple": (idx, 3)},
                rerun=1,
            )
            uids.append(mockplan.schedule(task=task, resource=pool_name))

        assert mockplan.run().run is True
        assert mockplan.report.passed is False
        assert mockplan.report.counter == {
            "passed": 2,
            "total": 3,
            "failed": 1,
        }

        assert mockplan.report.entries[0].name == "MultiTestParts"
        assert (
            mockplan.report.entries[1].name
            == "MultiTestParts - part(0/3) => Run 1"
        )
