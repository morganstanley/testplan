#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""Example to demonstrate PyUnit integration with Testplan."""

import sys
import unittest

from testplan import test_plan
from testplan.testing import pyunit


def before_start(env, result):
    result.log("Executing before start hook.")


def after_start(env, result):
    result.log("Executing after start hook.")


def before_stop(env, result):
    result.log("Executing before stop hook.")


def after_stop(env, result):
    result.log("Executing after stop hook.")


class TestAlpha(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/3/library/unittest.html).
    """

    def test_example(self):
        """Test with basic assertions."""
        self.assertTrue(True)
        self.assertFalse(False)


class TestBeta(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/3/library/unittest.html).
    """

    def test_fails(self):
        """Test that fails."""
        self.assertTrue(False)

    def test_raises(self):
        """Test that raises an Exception."""
        raise RuntimeError("Testcase raises")


@test_plan(name="PyUnit Example", description="Python unittest example")
def main(plan):
    # Now we are inside a function that will be passed a plan object, we
    # can add tests to this plan. Here we will add a unittest suite, made up
    # of a single TestCase defined above.
    plan.add(
        pyunit.PyUnit(
            name="My PyUnit",
            description="PyUnit example testcase",
            testcases=[TestAlpha, TestBeta],
            before_start=before_start,
            after_start=after_start,
            before_stop=before_stop,
            after_stop=after_stop,
        )
    )


# Finally we trigger our main function when the script is run, and
# set the return status.
if __name__ == "__main__":
    res = main()
    sys.exit(res.exit_code)
