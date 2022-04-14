#!/usr/bin/env python
"""
Example demonstrating usage of App driver to manually start it and stop it.
"""

import sys, re

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.app import App
from testplan.common.utils.match import LogMatcher


@testsuite
class MyTestsuite:
    """
    A testsuite that uses helper utilities in setup/teardown.
    """

    @testcase
    def manual_start(self, env, result):
        result.equal(env.cat_app.proc, None, description="App is not running.")

        env.cat_app.start()
        env.cat_app.wait(env.cat_app.status.STARTED)

        matcher = LogMatcher(log_path=env.cat_app.logpath)
        env.cat_app.proc.stdin.write(b"testplan\n")
        matched = matcher.match(re.compile(r"testplan"))
        result.true(matched, description="testplan in stdin")
        result.not_equal(env.cat_app.proc, None, description="App is running.")

        env.cat_app.stop()
        env.cat_app.wait(env.cat_app.status.STOPPED)

        result.equal(env.cat_app.proc, None, description="App is not running.")

    @testcase
    def manual_start_using_context_manager(self, env, result):
        result.equal(env.cat_app.proc, None, description="App is not running.")

        with env.cat_app:
            matcher = LogMatcher(log_path=env.cat_app.logpath)
            env.cat_app.proc.stdin.write(b"testplan\n")
            matched = matcher.match(re.compile(r"testplan"))
            result.true(matched, description="testplan in stdin")
            result.not_equal(
                env.cat_app.proc, None, description="App is running."
            )

        result.equal(env.cat_app.proc, None, description="App is not running.")


@test_plan(name="App driver example")
def main(plan):
    """
    A simple example that demonstrate manually starting and stopping the App driver.
    """
    plan.add(
        MultiTest(
            name="TestCat",
            suites=[MyTestsuite()],
            environment=[
                App(
                    name="cat_app",
                    binary="/bin/cat",
                    auto_start=False,
                )
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
