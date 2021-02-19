"""Test the interactive test runner."""
import six

if six.PY2:
    import mock
else:
    from unittest import mock

import pytest

from testplan import defaults
from testplan import report
from testplan import runners
from testplan import runnable
from testplan.common import entity
from testplan.testing import filtering
from testplan.testing import multitest
from testplan.testing import ordering
from testplan.runnable.interactive import base
from testplan.testing.multitest import driver
from testplan.common.utils.path import default_runpath


@multitest.testsuite
class Suite(object):
    """Test suite."""

    @multitest.testcase
    def case(self, env, result):
        """Testcase."""
        del env  # unused
        result.true(True)

    @multitest.testcase(parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase."""
        del env  # unused
        result.gt(val, 0)


def test_startup():
    """Test initializing and running the interactive runner."""
    target = runnable.TestRunner(name="TestRunner")
    mock_server = mock.MagicMock()

    with mock.patch(
        "cheroot.wsgi.Server", return_value=mock_server
    ), mock.patch(
        "testplan.runnable.interactive.reloader.ModuleReloader"
    ) as MockReloader:
        MockReloader.return_value = None

        irunner = base.TestRunnerIHandler(target)

        irunner.setup()
        assert irunner.target.runpath == default_runpath(target)

        mock_server.prepare.assert_called_once()
        mock_server.bind_addr = ("hostname", 1234)
        assert irunner.http_handler_info == mock_server.bind_addr

        irunner.run()
        mock_server.serve.assert_called_once()

        irunner.teardown()


@pytest.fixture
def irunner():
    """Set up an irunner instance for testing."""
    target = runnable.TestRunner(name="TestRunner")

    local_runner = runners.LocalRunner()
    test_uids = ["test_1", "test_2", "test_3"]
    test_objs = [
        multitest.MultiTest(
            name=uid,
            suites=[Suite()],
            test_filter=filtering.Filter(),
            test_sorter=ordering.NoopSorter(),
            stdout_style=defaults.STDOUT_STYLE,
            environment=[driver.Driver(name="mock_driver")],
        )
        for uid in test_uids
    ]

    for test in test_objs:
        local_runner.add(test, test.uid())

    target.resources.add(local_runner)

    with mock.patch("cheroot.wsgi.Server"), mock.patch(
        "testplan.runnable.interactive.reloader.ModuleReloader"
    ) as MockReloader:
        MockReloader.return_value = None

        irunner = base.TestRunnerIHandler(target)
        irunner.setup()

        yield irunner

        irunner.teardown()


@pytest.mark.parametrize("sync", [True, False])
def test_run_all_tests(irunner, sync):
    """Test running all tests."""
    _check_initial_report(irunner.report)

    ret = irunner.run_all_tests(await_results=sync)

    # If the tests were run asynchronously, await the results.
    if not sync:
        assert ret.result() is None

    # The report tree should have been updated as a side-effect.
    assert irunner.report.passed
    assert len(irunner.report.entries) == 3
    for test_report in irunner.report:
        assert test_report.passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_test(irunner, sync):
    """Test running a single test."""
    ret = irunner.run_test("test_1", await_results=sync)

    if not sync:
        assert ret.result() is None

    # The test report should have been updated as a side effect.
    assert irunner.report["test_1"].passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_suite(irunner, sync):
    """Test running a single test suite."""
    ret = irunner.run_test_suite("test_1", "Suite", await_results=sync)

    if not sync:
        assert ret.result() is None

    # The test report should have been updated as a side effect.
    assert irunner.report["test_1"]["Suite"].passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_testcase(irunner, sync):
    """Test running a single testcase."""
    ret = irunner.run_test_case("test_1", "Suite", "case", await_results=sync)

    if not sync:
        assert ret.result() is None

    # The test report should have been updated as a side effect.
    assert irunner.report["test_1"]["Suite"]["case"].passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_parametrization(irunner, sync):
    """Test running a single parametrization of a testcase."""
    ret = irunner.run_test_case(
        "test_1", "Suite", "parametrized__val_1", await_results=sync
    )

    if not sync:
        assert ret.result() is None

    # The test report should have been updated as a side effect.
    assert irunner.report["test_1"]["Suite"]["parametrized"][
        "parametrized__val_1"
    ].passed


@pytest.mark.parametrize("sync", [True, False])
def test_environment_control(irunner, sync):
    """Test starting and stopping test environments."""
    test = irunner.test("test_1")
    assert irunner.report["test_1"].env_status == entity.ResourceStatus.STOPPED

    # Start the environment and check it has the expected status.
    start_results = irunner.start_test_resources("test_1", await_results=sync)

    # If the environment was started asynchronously, wait for all of the
    # operations to copmlete before continuing.
    if not sync:
        start_results.result()

    assert test.resources.all_status(entity.ResourceStatus.STARTED)
    assert (
        test.resources.mock_driver.status.tag == entity.ResourceStatus.STARTED
    )
    assert irunner.report["test_1"].env_status == entity.ResourceStatus.STARTED

    # Stop the environment and check it has the expected status.
    stop_results = irunner.stop_test_resources("test_1", await_results=sync)

    # Again, await the async operation results if testing async.
    if not sync:
        stop_results.result()

    assert test.resources.all_status(entity.ResourceStatus.STOPPED)
    assert (
        test.resources.mock_driver.status.tag == entity.ResourceStatus.STOPPED
    )
    assert irunner.report["test_1"].env_status == entity.ResourceStatus.STOPPED


def _check_initial_report(initial_report):
    """
    Check that the initial report tree is generated correctly.

    First, check that there are three top-level Test reports.
    """
    assert initial_report.status == report.Status.UNKNOWN
    assert initial_report.runtime_status == report.RuntimeStatus.READY
    assert len(initial_report.entries) == 3
    for test_report in initial_report:
        # Each Test contains one suite.
        assert test_report.status == report.Status.UNKNOWN
        assert test_report.runtime_status == report.RuntimeStatus.READY
        assert len(test_report.entries) == 1
        for suite_report in test_report:
            # Each suite contains two testcase.
            assert suite_report.status == report.Status.UNKNOWN
            assert suite_report.runtime_status == report.RuntimeStatus.READY
            assert len(suite_report.entries) == 2

            # The first entry in the suite report is a regular testcase.
            testcase_report = suite_report.entries[0]
            assert isinstance(testcase_report, report.TestCaseReport)
            assert len(testcase_report.entries) == 0

            # The second entry in the suite report is a parametrized testcase.
            param_report = suite_report.entries[1]
            assert isinstance(param_report, report.TestGroupReport)
            assert len(param_report.entries) == 3
