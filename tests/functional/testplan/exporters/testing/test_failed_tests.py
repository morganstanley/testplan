import multiprocessing
import pathlib
import pytest
import threading
from testplan import TestplanMock
from testplan.common.utils import timing
from testplan.testing import multitest
from testplan.exporters.testing.failed_tests import (
    FailedTestsExporter,
    FailedTestLevel,
)
from testplan.runners.pools.base import Pool


@multitest.testsuite
class Alpha:
    def setup(self, env, result):
        result.log("within suite setup...")

    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "passing assertion")

    @multitest.testcase(parameters=(1, 2, 3))
    def test_param(self, env, result, arg):
        result.equal(arg, 2, f"failing assertion with arg {arg}")

    @multitest.testcase
    def test_fail(self, env, result):
        result.equal(1, 2, "failing assertion")


@multitest.testsuite
class Beta:
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.not_equal(5, 5)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


@multitest.testsuite
class Gamma:
    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "passing assertion")


@multitest.testsuite
class Delta:
    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "passing assertion")

    def teardown(self, env, result):
        raise Exception("foo")


@multitest.testsuite
class TimeoutSuite:
    @multitest.testcase
    def blocks(self, env, result):
        result.log("Blocking...")
        threading.Event().wait()


def failed_after_start(env, result):
    """
    This function is called after the test suite starts.
    It can be used to perform any necessary setup or checks.
    """
    result.fail("This is a failed after start function.")


@pytest.mark.parametrize(
    "level, failed_tests",
    (
        (FailedTestLevel.MULTITEST, ["alpha", "beta", "delta", "gamma"]),
        (
            FailedTestLevel.TESTSUITE,
            ["alpha:Alpha", "beta:Beta", "delta:Delta", "gamma"],
        ),
        (
            FailedTestLevel.TESTCASE,
            [
                "alpha:Alpha:test_fail",
                "alpha:Alpha:test_param <arg=1>",
                "alpha:Alpha:test_param <arg=3>",
                "beta:Beta:test_error",
                "beta:Beta:test_failure",
                "delta:Delta",
                "gamma",
            ],
        ),
    ),
)
def test_failed_tests_exporter(runpath, level, failed_tests):
    failed_tests_path = pathlib.Path(runpath) / "failed_tests.txt"
    plan = TestplanMock(
        "plan",
        exporters=FailedTestsExporter(
            dump_failed_tests=str(failed_tests_path), failed_tests_level=level
        ),
        runpath=runpath,
    )
    multitest_1 = multitest.MultiTest(name="alpha", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="beta", suites=[Beta()])
    multitest_3 = multitest.MultiTest(
        name="gamma", suites=[Gamma()], after_start=failed_after_start
    )
    multitest_4 = multitest.MultiTest(name="delta", suites=[Delta()])
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.add(multitest_3)
    plan.add(multitest_4)
    plan.run()
    assert failed_tests_path.exists()
    assert failed_tests_path.stat().st_size > 0, "Failed tests file is empty"
    with failed_tests_path.open("r") as f:
        content = f.read()
    assert "\n".join(failed_tests) == content.strip()


@pytest.mark.parametrize(
    "level, failed_tests",
    (
        (
            FailedTestLevel.MULTITEST,
            [
                "mock tests - part(0/3)",
                "mock tests - part(1/3)",
                "mock tests - part(2/3)",
            ],
        ),
        (FailedTestLevel.TESTSUITE, ["mock tests:Alpha", "mock tests:Beta"]),
        (
            FailedTestLevel.TESTCASE,
            [
                "mock tests:Alpha:test_fail",
                "mock tests:Alpha:test_param <arg=1>",
                "mock tests:Alpha:test_param <arg=3>",
                "mock tests:Beta:test_error",
                "mock tests:Beta:test_failure",
            ],
        ),
    ),
)
def test_failed_tests_exporter_with_parts(runpath, level, failed_tests):
    """
    Test the FailedTestsExporter with parts enabled.
    """
    failed_tests_path = pathlib.Path(runpath) / "failed_tests.txt"
    plan = TestplanMock(
        "plan",
        exporters=FailedTestsExporter(
            dump_failed_tests=str(failed_tests_path),
            failed_tests_level=level,
        ),
        runpath=runpath,
        parts=True,
    )
    multitest_1 = multitest.MultiTest(
        name="mock tests", suites=[Alpha(), Beta(), Gamma()], part=(0, 3)
    )
    multitest_2 = multitest.MultiTest(
        name="mock tests", suites=[Alpha(), Beta(), Gamma()], part=(1, 3)
    )
    multitest_3 = multitest.MultiTest(
        name="mock tests", suites=[Alpha(), Beta(), Gamma()], part=(2, 3)
    )
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.add(multitest_3)
    plan.run()
    assert failed_tests_path.exists()
    assert failed_tests_path.stat().st_size > 0, "Failed tests file is empty"
    with failed_tests_path.open("r") as f:
        content = f.read()
    assert "\n".join(failed_tests) == content.strip()


def _run_plan_timeout_in_process(failed_tests_path, runpath, use_parts):
    """
    Helper function to run the test plan in a separate process.
    Instantiate suites here to avoid pickling issues on Windows where multiprocessing uses spawn.
    """
    plan = TestplanMock(
        "plan",
        exporters=FailedTestsExporter(
            dump_failed_tests=str(failed_tests_path),
        ),
        runpath=runpath,
        timeout=5,
    )
    pool = Pool(name="pool", size=2)
    plan.add_resource(pool)

    if use_parts:
        for idx in range(2):
            plan.schedule(
                target=multitest.MultiTest(
                    name="mock tests 1",
                    suites=[TimeoutSuite(), Gamma()],
                    part=(idx, 2),
                ),
                resource="pool",
            )
    else:
        multitest_1 = multitest.MultiTest(
            name="mock tests 1", suites=[TimeoutSuite()]
        )
        multitest_2 = multitest.MultiTest(
            name="mock tests 2", suites=[Gamma()]
        )
        plan.schedule(target=multitest_1, resource="pool")
        plan.schedule(target=multitest_2, resource="pool")
    plan.run()


@pytest.mark.parametrize(
    "use_parts, expected_failed_test",
    (
        (False, "mock tests 1"),
        (True, "mock tests 1 - part(0/2)"),
    ),
)
def test_failed_tests_exporter_during_timeout(
    runpath, use_parts, expected_failed_test
):
    """
    Test the FailedTestsExporter for testplan timeout with and without parts.
    """
    failed_tests_path = pathlib.Path(runpath) / "failed_tests.txt"

    # this needs to be run in a separate process else _collect_timeout_info in TestRunner will face an error
    # causing the pool to not be aborted properly
    process = multiprocessing.Process(
        target=_run_plan_timeout_in_process,
        args=(failed_tests_path, runpath, use_parts),
    )
    process.start()
    try:
        timing.wait(
            failed_tests_path.exists,
            interval=1,
            timeout=60,
            raise_on_timeout=True,
        )
        process.join(timeout=15)
    finally:
        if process.is_alive():
            process.kill()

    assert failed_tests_path.exists()
    assert failed_tests_path.stat().st_size > 0, "Failed tests file is empty"
    with failed_tests_path.open("r") as f:
        content = f.read()
    assert expected_failed_test == content.strip()


def test_failed_tests_exporter_for_discarded_tasks(runpath):
    class RejectingPool(Pool):
        def __init__(self, *args, reject_task_name=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._reject_task_name = reject_task_name

        def _can_assign_task_to_worker(self, task, worker):
            test = task.materialize()
            if test.name == self._reject_task_name:
                return False
            return True

    failed_tests_path = pathlib.Path(runpath) / "failed_tests.txt"
    plan = TestplanMock(
        "plan",
        exporters=FailedTestsExporter(
            dump_failed_tests=str(failed_tests_path),
        ),
        runpath=runpath,
    )
    pool = RejectingPool(
        name="pool", size=1, reject_task_name="discarded test"
    )
    plan.add_resource(pool)

    discarded_mt = multitest.MultiTest(name="discarded test", suites=[Gamma()])
    normal_mt = multitest.MultiTest(name="normal test", suites=[Gamma()])

    plan.schedule(target=discarded_mt, resource="pool")
    plan.schedule(target=normal_mt, resource="pool")

    plan.run()

    assert failed_tests_path.exists()
    assert failed_tests_path.stat().st_size > 0, "Failed tests file is empty"
    with failed_tests_path.open("r") as f:
        content = f.read()
    assert "discarded test" == content.strip()
