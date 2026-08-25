#!/usr/bin/env python
"""
This example shows usage of the timeline assertion.
"""

import datetime
import sys

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase


@testsuite
class SampleSuite:
    @testcase
    def timeline_tests(self, env, result):
        start = datetime.datetime.now()

        result.timeline(
            {
                "Drivers": [
                    {
                        "name": "server",
                        "start": start,
                        "end": start + datetime.timedelta(seconds=1),
                    },
                    {
                        "name": "client",
                        "start": start + datetime.timedelta(milliseconds=200),
                        "end": start + datetime.timedelta(seconds=2),
                    },
                    {
                        "name": "worker",
                        "start": start + datetime.timedelta(seconds=1),
                        "end": start + datetime.timedelta(seconds=3),
                    },
                ]
            },
            description="Sample Timeline",
        )


@test_plan(name="Timeline Example")
def main(plan):
    plan.add(
        MultiTest(name="Timeline Assertions Test", suites=[SampleSuite()])
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
