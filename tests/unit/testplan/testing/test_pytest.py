"""Unit tests for PyTest runner."""
import collections
import os

import pytest

from testplan import defaults, report
from testplan.report import TestCaseReport
from testplan.testing import py_test as pytest_runner
from tests.unit.testplan.testing import pytest_expected_data


@pytest.fixture
def pytest_test_inst(repo_root_path, root_directory):
    """Return a PyTest test instance, with the example tests as its target."""
    # For testing purposes, we want to run the pytest example at
    # examples/PyTest/pytest_tests.py.
    example_path = os.path.join(
        repo_root_path, "examples", "PyTest", "pytest_tests.py"
    )

    rootdir = os.path.commonprefix([root_directory, os.getcwd()])

    # We need to explicitly set the stdout_style in UT, normally it is inherited
    # from the parent object but that doesn't work when testing PyTest in
    # isolation.
    return pytest_runner.PyTest(
        name="My PyTest",
        description="PyTest example test",
        target=example_path,
        stdout_style=defaults.STDOUT_STYLE,
        extra_args=["--rootdir", rootdir],
    )


def test_dry_run(pytest_test_inst):
    """
    Test the dry_run() method returns the expected report skeleton.
    """
    result = pytest_test_inst.dry_run()
    report = result.report
    assert report == pytest_expected_data.EXPECTED_DRY_RUN_REPORT


def test_run_tests(pytest_test_inst):
    """Test running all tests in batch mode."""
    pytest_test_inst.setup()
    pytest_test_inst.run_tests()

    assert pytest_test_inst.report.status == report.Status.FAILED
    _check_attachements(
        pytest_test_inst.result.report["pytest_tests.py::TestWithAttachments"][
            "test_attachment"
        ]
    )
    _check_all_testcounts(pytest_test_inst.report.counter)


def test_run_testcases_iter_all(pytest_test_inst):
    """Test running all tests iteratively."""
    all_results = list(pytest_test_inst.run_testcases_iter())
    assert len(all_results) == 14

    report_attributes, current_uids = all_results[0]
    assert current_uids == ["My PyTest"]
    assert report_attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    counter = collections.Counter()
    for testcase_report, _ in all_results[1:]:
        counter[testcase_report.status.value] += 1
    _check_all_testcounts(counter)

    testcase_report, _ = all_results[7]
    _check_attachements(testcase_report)


def test_run_testcases_iter_testsuite(pytest_test_inst):
    """Test running a single testsuite iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics"
        )
    )
    assert len(all_results) == 6

    report_attributes, current_uids = all_results[0]
    assert current_uids == ["My PyTest", "pytest_tests.py::TestPytestBasics"]
    assert report_attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    counter = collections.Counter()
    for testcase_report, _ in all_results[1:]:
        counter[testcase_report.status.value] += 1
        counter["total"] += 1

    assert counter["total"] == 5
    assert counter["passed"] == 4
    assert counter["failed"] == 1
    assert counter["skipped"] == 0


def test_run_testcases_iter_testcase(pytest_test_inst):
    """Test running a single testcase iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics",
            testcase_pattern="test_success",
        )
    )
    assert len(all_results) == 2

    report_attributes, current_uids = all_results[0]
    assert current_uids == [
        "My PyTest",
        "pytest_tests.py::TestPytestBasics",
        "test_success",
    ]
    assert report_attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    testcase_report, parent_uids = all_results[1]
    assert testcase_report.status == report.Status.PASSED
    assert parent_uids == ["My PyTest", "pytest_tests.py::TestPytestBasics"]


def test_run_testcases_iter_param(pytest_test_inst):
    """Test running all parametrizations of a testcase iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics",
            testcase_pattern="test_parametrization",
        )
    )
    assert len(all_results) == 4

    report_attributes, current_uids = all_results[0]
    assert current_uids == [
        "My PyTest",
        "pytest_tests.py::TestPytestBasics",
        "test_parametrization",
    ]
    assert report_attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    counter = collections.Counter()
    for testcase_report, parent_uids in all_results[1:]:
        assert parent_uids == [
            "My PyTest",
            "pytest_tests.py::TestPytestBasics",
            "test_parametrization",
        ]
        counter[testcase_report.status.value] += 1
        counter["total"] += 1

    assert counter["total"] == 3
    assert counter["passed"] == 3
    assert counter["failed"] == 0
    assert counter["skipped"] == 0


def test_capture_stdout(pytest_test_inst):
    """Test running a single testcase iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics",
            testcase_pattern="test_failure",
        )
    )
    assert all_results[0][0]["runtime_status"] == report.RuntimeStatus.RUNNING
    assert all_results[1][0].entries[1]["message"] == "test output\n"


def _check_attachements(report: TestCaseReport):
    assert len(report.attachments) == 1
    assert report.attachments[0].description == "example attachment"


def _check_all_testcounts(counter):
    """Check the pass/fail/skip counts after running all tests."""
    # One testcase is conditionally skipped when not running on a posix OS, so
    # we have to take this into account when checking the pass/fail/skip counts.
    if os.name == "posix":
        assert counter["passed"] == 8
        assert counter["skipped"] == 1
    else:
        assert counter["passed"] == 7
        assert counter["skipped"] == 2

    assert counter["failed"] == 4
