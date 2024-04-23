#!/usr/bin/env python
"""
Example demonstrating usage of testplan.common.utils.helper module.
By using the helper functions and/or the prefedined Testsuite, the user can
readily add additional information of Testplan execution to the report.
"""

import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.app import App
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


def after_stop_fn(env, result):
    # Attach drivers' log files if the multitest failed.
    stdout_logger = helper.DriverLogCollector(
        file_pattern=["stdout*"], description="stdout"
    )
    stderr_logger = helper.DriverLogCollector(
        file_pattern=["stderr*"], description="stderr"
    )

    stdout_logger(env, result)
    stderr_logger(env, result)

    # Delete Multitest level runpath if the multitest passed.
    # This function cleans the runpath before the exporters
    # have chance collecting the files, hence commented out.
    # helper.clean_runpath_if_passed(env, result)


def error_handler_fn(env, result):
    # This will be executed when a step hits an exception.
    # Raise an exception in an Environment step or Multitest/Suite/Test hooks to try.
    step_results = env._environment.parent.result.step_results
    if "run_tests" in step_results:
        [
            result.log(log, description="Error log")
            for log in step_results["run_tests"].flattened_logs
            if log["levelname"] == "ERROR"
        ]
    [
        result.log(log, description="Error log")
        for (
            key,
            log,
        ) in env._environment.parent.resources.start_exceptions.items()
    ]
    [
        result.log(log, description="Error log")
        for (
            key,
            log,
        ) in env._environment.parent.resources.stop_exceptions.items()
    ]
    result.log("Error handler ran!")


@test_plan(name="Example using helper")
def main(plan):
    """
    Add a MultiTest that uses helper utilities in before_start/after_stop hooks.
    """
    plan.add(
        MultiTest(
            name="HelperTest",
            suites=[
                # This is a pre-defined testsuite that logs info to report
                helper.TestplanExecutionInfo(),
                MyTestsuite(),
            ],  # shortcut: suites=[helper.TestplanExecutionInfo()]
            environment=[App("echo", binary="/bin/echo", args=["testplan"])],
            before_start=before_start_fn,
            after_stop=after_stop_fn,
            error_handler=error_handler_fn,
        )
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
