"""Test the interactive test runner."""
from copy import deepcopy
from unittest import mock

import pytest

from testplan import defaults
from testplan import report
from testplan import runnable
from testplan.common import entity
from testplan.report import RuntimeStatus, TestCaseReport
from testplan.testing import filtering
from testplan.testing import multitest
from testplan.testing import ordering
from testplan.testing.multitest import driver
from testplan.runnable.interactive import base
from testplan.common.utils.path import default_runpath
from testplan.common.utils.testing import check_report
from testplan.runners.local import LocalRunner


@multitest.testsuite
class Suite:
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


@multitest.testsuite(tags="foo")
class TaggedSuite:
    """Test suite."""

    @multitest.testcase(tags="bar")
    def case(self, env, result):
        """Testcase."""
        del env  # unused
        result.true(True)

    @multitest.testcase
    def ignored(self, env, result):
        """Testcase which will be filtered out."""
        pass

    @multitest.testcase(tags="baz", parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase."""
        del env  # unused
        result.gt(val, 0)


@multitest.testsuite
class FailedSetupSuite:
    """Test suite with a failing setup method."""

    def setup(self, env, result):
        result.fail("Failing for a reason.")

    @multitest.testcase
    def case_a(self, env, result):
        result.equal(5, 5)

    @multitest.testcase
    def case_b(self, env, result):
        result.not_equal(5, 5)

    def teardown(self, env, result):
        result.fail("Failing for yet another reason.")


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

    local_runner = LocalRunner()
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


def test_run_suite_with_failed_setup():
    target = runnable.TestRunner(name="TestRunner")

    local_runner = LocalRunner()
    test = multitest.MultiTest(
        name="MT",
        suites=[FailedSetupSuite()],
        test_filter=filtering.Filter(),
        test_sorter=ordering.NoopSorter(),
        stdout_style=defaults.STDOUT_STYLE,
    )
    local_runner.add(test, test.uid())
    target.resources.add(local_runner)

    with mock.patch("cheroot.wsgi.Server"), mock.patch(
        "testplan.runnable.interactive.reloader.ModuleReloader"
    ) as MockReloader:
        MockReloader.return_value = None

        irunner = base.TestRunnerIHandler(target)
        irunner.setup()

        irunner.run_test_suite("MT", "FailedSetupSuite", await_results=True)
        assert irunner.report.failed
        for testcase_report in irunner.report.entries[0].entries[0].entries:
            if testcase_report.name in ["setup", "teardown"]:
                assert testcase_report.runtime_status == RuntimeStatus.FINISHED
            else:
                assert testcase_report.runtime_status == RuntimeStatus.NOT_RUN
        irunner.teardown()


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
    ret = irunner.run_test_case_param(
        "test_1",
        "Suite",
        "parametrized",
        "parametrized__val_1",
        await_results=sync,
    )

    if not sync:
        assert ret.result() is None

    # The test report should have been updated as a side effect.
    assert irunner.report["test_1"]["Suite"]["parametrized"][
        "parametrized__val_1"
    ].passed


@pytest.mark.parametrize("sync", [True, False])
def test_run_parametrization_all(irunner, sync):
    """Test running all the parametrization of a parametrization group."""
    ret = irunner.run_test_case(
        "test_1", "Suite", "parametrized", await_results=sync
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
    # operations to complete before continuing.
    if not sync:
        start_results.result()

    assert test.resources.all_status(entity.ResourceStatus.STARTED)
    assert test.resources.mock_driver.status == entity.ResourceStatus.STARTED
    assert irunner.report["test_1"].env_status == entity.ResourceStatus.STARTED

    # Stop the environment and check it has the expected status.
    stop_results = irunner.stop_test_resources("test_1", await_results=sync)

    # Again, await the async operation results if testing async.
    if not sync:
        stop_results.result()

    assert test.resources.all_status(entity.ResourceStatus.STOPPED)
    assert test.resources.mock_driver.status == entity.ResourceStatus.STOPPED
    assert irunner.report["test_1"].env_status == entity.ResourceStatus.STOPPED


@pytest.mark.parametrize(
    "tags,num_of_suite_entries", ((("foo",), 3), (("bar", "baz"), 2))
)
def test_run_all_tagged_tests(tags, num_of_suite_entries):
    """Test running all tests whose testcases are selected by tags."""
    target = runnable.TestRunner(name="TestRunner")

    local_runner = LocalRunner()
    test_uids = ["test_1", "test_2", "test_3"]
    test_objs = [
        multitest.MultiTest(
            name=uid,
            suites=[TaggedSuite()],
            test_filter=filtering.Tags({"simple": set(tags)}),
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

        irunner.run_all_tests(await_results=True)
        assert irunner.report.passed
        assert len(irunner.report.entries) == 3
        for test_report in irunner.report:
            assert test_report.passed
            assert len(test_report.entries) == 1
            assert len(test_report.entries[0].entries) == num_of_suite_entries
            assert len(test_report.entries[0].entries[-1].entries) == 3

        irunner.teardown()


def test_initial_report(irunner):
    """
    Check that the initial report tree is generated correctly.
    """
    initial_report = irunner.report
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


def test_reload_report(irunner):
    """
    Tests report reload of the interactive handler.
    """
    # We run one of the MultiTests, the suite for another, and a testcase
    # and one of the parametrized testcases for the third.
    irunner.run_test("test_1", await_results=True)
    irunner.run_test_suite("test_2", "Suite", await_results=True)
    irunner.run_test_case("test_3", "Suite", "case", await_results=True)
    irunner.run_test_case_param(
        "test_1",
        "Suite",
        "parametrized",
        "parametrized__val_2",
        await_results=True,
    )
    # Now we modify the reports forcefully
    # In test_1, we take no action
    # In test_2, we remove "parametrized" it needs to be added back, and we
    # add "new_case" that should be removed
    del irunner.report["test_2"]["Suite"]["parametrized"]
    irunner.report["test_2"]["Suite"]["new_case"] = TestCaseReport(
        name="new_case", uid="new_case"
    )
    # In test_3, we update "parametrized" by removing "3" and adding
    # "4", the former will be added back the latter will be removed
    del irunner.report["test_3"]["Suite"]["parametrized"][
        "parametrized__val_3"
    ]
    irunner.report["test_3"]["Suite"]["parametrized"][
        "parametrized__val_4"
    ] = TestCaseReport(
        name="parametrized <val=4>",
        uid="parametrized__val_4",
    )

    # We preserve the current report
    old_report = deepcopy(irunner.report)

    # We reload and assert
    irunner.reload_report()

    for test in irunner.report:
        # A MultiTest should reset to ready upon changes underneath
        assert test.runtime_status == (
            RuntimeStatus.FINISHED
            if test.uid == "test_1"
            else RuntimeStatus.READY
        )
        for suite in irunner.report[test.uid]:
            # A testsuite should reset to ready upon changes underneath
            assert suite.runtime_status == (
                RuntimeStatus.FINISHED
                if test.uid == "test_1"
                else RuntimeStatus.READY
            )
            for index, entry in enumerate(suite):
                # We need to check explicitly both "case" and "parametrized"
                assert entry.uid == ("parametrized" if index else "case")
                if entry.uid == "case":
                    check_report(
                        old_report[test.uid][suite.uid][entry.uid],
                        irunner.report[test.uid][suite.uid][entry.uid],
                    )
                elif entry.uid == "parametrized":
                    for param_index, param in enumerate(entry):
                        assert (
                            param.uid
                            == [
                                f"parametrized__val_{i + 1}" for i in range(3)
                            ][param_index]
                        )
                        if (test.uid == "test_1") or (
                            test.uid == "test_3"
                            and param.uid != "parametrized__val_3"
                        ):
                            check_report(
                                old_report[test.uid][suite.uid][entry.uid][
                                    param.uid
                                ],
                                irunner.report[test.uid][suite.uid][entry.uid][
                                    param.uid
                                ],
                            )
