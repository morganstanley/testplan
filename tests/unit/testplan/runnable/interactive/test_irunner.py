"""Test the interactive test runner."""
import mock
import pytest

from testplan.runnable.interactive import base
from testplan import report
from testplan.common import entity
from testplan import runners
from testplan.testing import multitest


@multitest.testsuite
class Suite(object):
    """Test suite."""

    @multitest.testcase
    def case(self, env, result):
        """Testcase."""
        del env  # unused
        result.true(True)


def test_startup():
    """Test initializing and running the interactive runner."""
    target = mock.MagicMock()
    mock_server = mock.MagicMock()

    with mock.patch("cheroot.wsgi.Server", return_value=mock_server):
        irunner = base.TestRunnerIHandler(target)

        irunner.setup()
        mock_server.prepare.assert_called_once()
        mock_server.bind_addr = ("hostname", 1234)
        assert irunner.http_handler_info == mock_server.bind_addr

        irunner.run()
        mock_server.serve.assert_called_once()

        irunner.teardown()


@pytest.fixture
def irunner():
    """Set up an irunner instance for testing."""
    target = mock.MagicMock()

    local_runner = runners.LocalRunner()
    test_uids = ["test_1", "test_2", "test_3"]
    test_objs = [
        multitest.MultiTest(name=uid, suites=[Suite()])
        for uid in test_uids
    ]

    for test in test_objs:
        local_runner.add(test, test.uid())

    target.resources = entity.Environment()
    target.resources.add(local_runner)

    with mock.patch("cheroot.wsgi.Server"):
        irunner = base.TestRunnerIHandler(target)
        irunner.setup()

        yield irunner

        irunner.teardown()


@pytest.mark.parametrize("sync", [True, False])
def test_run_all_tests(irunner, sync):
    """Test running all tests."""
    _check_initial_report(irunner.report)

    results = irunner.run_all_tests(await_results=sync)
    assert len(results) == 3
    for res in results:
        # If tests were run synchronously, we should have the report objects.
        # Otherwise, we will have async result objects which we can await.
        if sync:
            test_report = res
        else:
            test_report = res.get()
        assert isinstance(test_report, report.TestGroupReport)
        assert test_report.passed

    # The test report should have been updated as a side effect.
    assert irunner.report.passed
    for test_report in irunner.report:
        assert test_report.passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_test(irunner, sync):
    """Test running a single test."""
    results = irunner.run_test("test_1", await_results=sync)
    assert len(results) == 1

    # If tests were run synchronously, we should have the report objects.
    # Otherwise, we will have async result objects which we can await.
    if sync:
        test_report = results[0]
    else:
        test_report = results[0].get()

    assert isinstance(test_report, report.TestGroupReport)
    assert test_report.passed

    # The test report should have been updated as a side effect.
    assert irunner.report.status == report.Status.READY
    for test_report in irunner.report:
        if test_report.uid == "test_1":
            assert test_report.passed
        else:
            assert test_report.status == report.Status.READY


@pytest.mark.parametrize("sync", [True, False])
def test_run_suite(irunner, sync):
    """Test running a single test suite."""
    results = irunner.run_test_suite("test_1", "Suite", await_results=sync)
    assert len(results) == 1

    # If tests were run synchronously, we should have the report objects.
    # Otherwise, we will have async result objects which we can await.
    if sync:
        test_report = results[0]
    else:
        test_report = results[0].get()

    assert isinstance(test_report, report.TestGroupReport)
    assert test_report.passed

    # The test report should have been updated as a side effect.
    assert irunner.report.status == report.Status.READY
    for test_report in irunner.report:
        if test_report.uid == "test_1":
            assert test_report.passed
        else:
            assert test_report.status == report.Status.READY


@pytest.mark.parametrize("sync", [True, False])
def test_run_testcase(irunner, sync):
    """Test running a single testcase."""
    results = irunner.run_test_case(
        "test_1", "Suite", "case", await_results=sync,
    )
    assert len(results) == 1

    # If tests were run synchronously, we should have the report objects.
    # Otherwise, we will have async result objects which we can await.
    if sync:
        test_report = results[0]
    else:
        test_report = results[0].get()

    assert isinstance(test_report, report.TestGroupReport)
    assert test_report.passed

    # The test report should have been updated as a side effect.
    assert irunner.report.status == report.Status.READY
    for test_report in irunner.report:
        if test_report.uid == "test_1":
            assert test_report.passed
        else:
            assert test_report.status == report.Status.READY


def _check_initial_report(initial_report):
    """
    Check that the initial report tree is generated correctly.

    First, check that there are three top-level Test reports.
    """
    assert initial_report.status == report.Status.READY
    assert len(initial_report.entries) == 3
    for test_report in initial_report:
        # Each Test contains one suite.
        assert test_report.status == report.Status.READY
        assert len(test_report.entries) == 1
        for suite_report in test_report:
            # Each suite contains one testcase.
            assert suite_report.status == report.Status.READY
            assert len(suite_report.entries) == 1

