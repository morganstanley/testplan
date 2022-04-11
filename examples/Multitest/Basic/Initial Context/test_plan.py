#!/usr/bin/env python
"""
    A Simple example to show how to access data from initial context passed
    to MultiTest constructor.

    Initial context should be a dictionary, which will be available in
      - Driver.context in driver instances, together with all the started drivers so far
      - env in testcases together with all the drivers
"""

from testplan import test_plan
from testplan.testing.multitest import testsuite, testcase, MultiTest
from testplan.testing.multitest.driver import Driver

TEST_CONTEXT_VALUE = "Data in context"

INITIAL_CONTEXT = {"test_value": TEST_CONTEXT_VALUE}


@testsuite
class SimpleSuite:
    @testcase
    def test_initial_context_access(self, env, result):
        """
        env in the testcase has the content of the initial context plus the drivers
        """
        result.equal(env.test_value, TEST_CONTEXT_VALUE)

    @testcase
    def test_driver_captured_data(self, env, result):
        """
        Just to validate the driver captured the data from context during it's startup
        """
        result.equal(env.context_user.value_from_context, TEST_CONTEXT_VALUE)


class ContextUser(Driver):
    """
    A driver that shows how to access the initial context from a driver.
    Driver.context is prepopulated with the initial_context from the plan
    plus the drivers already started
    """

    def __init__(self, **options):
        super(ContextUser, self).__init__(**options)

        self.value_from_context = None

    def starting(self):
        self.value_from_context = (
            self.context.test_value
        )  # just grab the value from self.context


@test_plan(name="Initial context example")
def main(plan):

    plan.add(
        MultiTest(
            "Initial Context example",
            [SimpleSuite()],
            environment=[ContextUser(name="context_user")],
            initial_context=INITIAL_CONTEXT,
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
