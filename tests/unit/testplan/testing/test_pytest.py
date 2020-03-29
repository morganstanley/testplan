"""Unit tests for PyTest runner."""
import collections
import json
import os

import pytest

from testplan.testing import py_test as pytest_runner
import testplan.report
from testplan import defaults

from tests.unit.testplan.testing import pytest_expected_data


@pytest.fixture
def pytest_test_inst(repo_root_path):
    """Return a PyTest test instance, with the example tests as its target."""
    # For testing purposes, we want to run the pytest example at
    # examples/PyTest/pytest_tests.py.
    example_path = os.path.join(
        repo_root_path, "examples", "PyTest", "pytest_tests.py"
    )

    rootdir = os.path.commonprefix([str(pytest.config.rootdir), os.getcwd()])

    # We need to explicitly set the stdout_style in UT, normally it is inherited
    # from the parent object but that doesn't work when testing PyTest in
    # isolation.
    return pytest_runner.PyTest(
        name="pytest example",
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
    report = pytest_test_inst.report

    assert report.status == testplan.report.Status.FAILED
    _check_all_testcounts(report.counter)


def test_run_testcases_iter_all(pytest_test_inst):
    """Test running all tests iteratively."""
    all_results = list(pytest_test_inst.run_testcases_iter())
    assert len(all_results) == 12

    counter = collections.Counter()
    for report, _ in all_results:
        counter[report.status] += 1

    _check_all_testcounts(counter)


def test_run_testcases_iter_testsuite(pytest_test_inst):
    """Test running a single testsuite iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics"
        )
    )
    assert len(all_results) == 5

    counter = collections.Counter()
    for report, _ in all_results:
        counter[report.status] += 1
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
    assert len(all_results) == 1
    report, parent_uids = all_results[0]

    assert report.status == testplan.report.Status.PASSED
    assert parent_uids == [
        "pytest example",
        "pytest_tests.py::TestPytestBasics",
    ]


def test_run_testcases_iter_param(pytest_test_inst):
    """Test running all parametrizations of a testcase iteratively."""
    all_results = list(
        pytest_test_inst.run_testcases_iter(
            testsuite_pattern="pytest_tests.py::TestPytestBasics",
            testcase_pattern="test_parametrization",
        )
    )
    assert len(all_results) == 3

    counter = collections.Counter()
    for report, parent_uids in all_results:
        assert parent_uids == [
            "pytest example",
            "pytest_tests.py::TestPytestBasics",
            "test_parametrization",
        ]
        counter[report.status] += 1
        counter["total"] += 1

    assert counter["total"] == 3
    assert counter["passed"] == 3
    assert counter["failed"] == 0
    assert counter["skipped"] == 0


def _check_all_testcounts(counter):
    """Check the pass/fail/skip counts after running all tests."""
    # One testcase is conditionally skipped when not running on a posix OS, so
    # we have to take this into account when checking the pass/fail/skip counts.
    if os.name == "posix":
        assert counter["passed"] == 7
        assert counter["skipped"] == 1
    else:
        assert counter["passed"] == 6
        assert counter["skipped"] == 2

    assert counter["failed"] == 4
