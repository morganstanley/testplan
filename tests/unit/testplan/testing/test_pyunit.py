"""Unit tests for the PyUnit test runner."""

import unittest

from testplan.testing import pyunit
from testplan.testing import filtering
from testplan.testing import ordering
from testplan import defaults

# TODO: shouldn't need to specify these...
PYUNIT_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


class Passing(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/2/library/unittest.html).
    """

    def asserts(self):
        """Test with basic assertions."""
        self.assertTrue(True)
        self.assertFalse(False)


def test_run_tests():
    test_runner = pyunit.PyUnit(
        name="My PyUnit",
        description="PyUnit example testcase",
        suites=[unittest.makeSuite(Passing)],
        **PYUNIT_DEFAULT_PARAMS
    )
    result = test_runner.run()
    report = result.report
    assert report.passed
