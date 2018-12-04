#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""Example to demonstrate PyTest integration with Testplan."""
import sys

import testplan
from testplan.testing import py_test


# We specify a description for the testplan, as well as a database to which
# the report should be committed. It is useful to specify a database, even
# if you don't intend for the results to be persisted : the cost is negligible
# and it provides an easily shared and detailed view of the test results.
# noinspection PyUnresolvedReferences
@testplan.test_plan(name='PyTestExample',
                    description='PyTest basic example')
def main(plan):
    # Now we are inside a function that will be passed a plan object, we
    # can add tests to this plan. Here we will add a PyTest instance that
    # targets the tests in pytest_basics.py.
    plan.add(py_test.PyTest(
        name='PyTest',
        description='PyTest example - pytest basics',
        target=['pytest_tasks.py']))


# Finally we trigger our main function when the script is run, and
# set the return status. Note that it has to be inverted because it's
# a boolean value.
if __name__ == '__main__':
    res = main()
    sys.exit(res.exit_code)
