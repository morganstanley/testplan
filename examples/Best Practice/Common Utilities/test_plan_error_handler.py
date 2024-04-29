#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
Example demonstrating usage of Multitest's error_handler hook.
By using the error_handler hook users can clean-up resources and
add additional information to the report upon unexpected Exceptions.
"""

import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.base import Driver
from testplan.common.utils import helper


@testsuite
class MyTestsuite:
    """
    A testsuite that uses helper utilities in setup/teardown.
    """

    def setup(self, env, result):
        # Save host environment variable in report.
        helper.log_environment(result)

        # Save current path & command line arguments in report.
        helper.log_pwd(result)
        helper.log_cmd(result)

        # Save host hardware information in report.
        helper.log_hardware(result)

    @testcase
    def my_testcase(self, env, result):
        # Add your testcase here
        result.true(True)

    def teardown(self, env, result):
        """
        Attach testplan.log file in report.
        """
        helper.attach_log(result)


def before_start_fn(env, result):
    # Save host environment variable in report.
    helper.log_environment(result)

    # Save current path & command line arguments in report.
    helper.log_pwd(result)


def error_handler_fn(env, result):
    # This will be executed when a step hits an exception.
    step_results = env._environment.parent.result.step_results
    if "run_tests" in step_results:
        for log in step_results["run_tests"].flattened_logs:
            if log["levelname"] == "ERROR":
                result.log(log, description="Error log")
    result.log("Error handler ran!")


class FailingStopDriver(Driver):
    def pre_stop(self):
        raise Exception("Exception raised to trigger error handler hook!")


@test_plan(name="Example running error_handler")
def main(plan):
    """
    Add a MultiTest that triggers error_handler hook.
    """
    plan.add(
        MultiTest(
            name="ErrorHandlerTest",
            suites=[
                # This is a pre-defined testsuite that logs info to report
                helper.TestplanExecutionInfo(),
                MyTestsuite(),
            ],  # shortcut: suites=[helper.TestplanExecutionInfo()]
            environment=[FailingStopDriver("Dummy")],
            before_start=before_start_fn,
            error_handler=error_handler_fn,
        )
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
