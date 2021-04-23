#!/usr/bin/env python
"""
Example demonstrating usage of App driver to start an arbitrary binary as subprocess
- /bin/echo in this case - and checks its stdout output and return code.
"""

import sys, re

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver.app import App
from testplan.common.utils.match import LogMatcher


@testsuite
class MyTestsuite(object):
    """
    A testsuite that uses helper utilities in setup/teardown.
    """

    @testcase
    def my_testcase(self, env, result):
        matcher = LogMatcher(log_path=env.echo.outpath)
        matched = matcher.match(re.compile(r"testplan"))
        result.true(matched, description="testplan in stdout")
        env.echo.proc.stdin.write(b"finish\n")


def after_stop_fn(env, result):
    result.equal(env.echo.retcode, 0, description="echo exit with 0")


@test_plan(name="App driver example")
def main(plan):
    """
    A simple example that demonstrate App driver usage. App prints 'testplan' to
    standard output on startup and then waits for a user input simulating a long running app.
    """
    plan.add(
        MultiTest(
            name="TestEcho",
            suites=[MyTestsuite()],
            environment=[
                App(
                    "echo",
                    binary="echo.sh",
                    shell=True,
                    stdout_regexps=[
                        re.compile(r"testplan")
                    ],  # argument inherited from Driver class
                )
            ],
            after_stop=after_stop_fn,
        )
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
