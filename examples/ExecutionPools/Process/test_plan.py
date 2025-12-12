#!/usr/bin/env python
"""
This example is to demonstrate parallel test execution in a process pool.
"""

import sys

from testplan import test_plan
from testplan import Task
from testplan.runners.pools.process import ProcessPool

from testplan.parser import TestplanParser
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


class CustomParser(TestplanParser):
    """Inheriting base parser."""

    def add_arguments(self, parser):
        """Defining custom arguments for this Testplan."""
        parser.add_argument("--tasks-num", action="store", type=int, default=8)
        parser.add_argument("--pool-size", action="store", type=int, default=4)


# Using a custom parser to support `--tasks-num` and `--pool-size` command
# line arguments so that users can experiment with process pool test execution.


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="ProcessPoolExecution",
    parser=CustomParser,
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    # Add a process pool test execution resource to the plan of given size.
    pool = ProcessPool(name="MyPool", size=plan.args.pool_size)
    plan.add_resource(pool)

    # Add a given number of similar tests to the process pool
    # to be executed in parallel.
    for idx in range(plan.args.tasks_num):
        # All Task arguments need to be serializable.
        task = Task(
            target="make_multitest", module="tasks", kwargs={"index": idx}
        )
        plan.schedule(task, resource="MyPool")


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
