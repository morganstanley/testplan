#!/usr/bin/env python
"""Example to demonstrate PyUnit integration with Testplan."""

import sys
import testplan
import unittest
from testplan.testing import pyunit


class MyTest(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/2/library/unittest.html).
    """

    def test_example(self):
        """Test with basic assertions."""
        self.assertTrue(True)
        self.assertFalse(False)


@testplan.test_plan(name="PyUnit", description="UnitTest example")
def main(plan):
    # Now we are inside a function that will be passed a plan object, we
    # can add tests to this plan. Here we will add a unittest suite, made up
    # of a single TestCase defined above.
    plan.add(
        pyunit.PyUnit(
            name="My PyUnit",
            description="PyUnit example testcase",
            suites=[unittest.makeSuite(MyTest)],
        )
    )


# Finally we trigger our main function when the script is run, and
# set the return status.
if __name__ == "__main__":
    res = main()
    sys.exit(res.exit_code)
