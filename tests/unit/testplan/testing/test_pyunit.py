"""Unit tests for the PyUnit test runner."""

import unittest
import pytest

from testplan.testing import pyunit
from testplan.testing import filtering
from testplan.testing import ordering
from testplan import defaults

PYUNIT_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


@pytest.mark.skip("Example PyUnit testsuite")
class Passing(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/2/library/unittest.html).
    """

    def test_asserts(self):
        """Test with basic assertions."""
        self.assertTrue(True)
        self.assertFalse(False)


@pytest.mark.skip("Example PyUnit testsuite")
class Failing(unittest.TestCase):
    def test_asserts_false(self):
        """Assert False is True."""
        self.assertTrue(False)

    def test_raises(self):
        """Raises an Exception."""
        raise RuntimeError("Boom")


def test_passing_tests():
    """Test running a basic testsuite which should pass."""
    test_runner = pyunit.PyUnit(
        name="My PyUnit",
        description="PyUnit example testcase",
        suite=unittest.makeSuite(Passing),
        **PYUNIT_DEFAULT_PARAMS
    )
    result = test_runner.run()
    report = result.report
    assert report.passed
    assert len(report.entries) == 1

    testcase_report = report.entries[0]
    assert testcase_report.passed
    assert len(testcase_report.entries) == 1

    log_entry = testcase_report.entries[0]
    assert log_entry["type"] == "Log"
    assert log_entry["message"] == "All PyUnit testcases passed"


def test_failing_tests():
    """Test running a basic testsuite which should fail."""
    test_runner = pyunit.PyUnit(
        name="My PyUnit",
        description="PyUnit example testcase",
        suite=unittest.makeSuite(Failing),
        **PYUNIT_DEFAULT_PARAMS
    )
    result = test_runner.run()
    report = result.report
    assert not report.passed
    assert len(report.entries) == 1

    testcase_report = report.entries[0]
    assert not testcase_report.passed
    assert len(testcase_report.entries) == 2

    error_entry = testcase_report.entries[0]
    assert "RuntimeError: Boom" in error_entry["content"]
    assert "test_raises" in error_entry["description"]

    fail_entry = testcase_report.entries[1]
    assert "AssertionError: False is not true" in fail_entry["content"]
    assert "test_asserts_false" in fail_entry["description"]
