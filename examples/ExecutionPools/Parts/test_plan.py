#!/usr/bin/env python
"""
This example is to demonstrate parallel test execution with parts in a pool.
"""

import sys

from testplan import test_plan, Task
from testplan.parser import TestplanParser
from testplan.runners.pools import ThreadPool
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


class CustomParser(TestplanParser):
    """Inheriting base parser."""

    def add_arguments(self, parser):
        """Defining custom arguments for this Testplan."""
        parser.add_argument(
            "--parts-num",
            action="store",
            type=int,
            default=3,
            help="Number of parts to be split.",
        )
        parser.add_argument(
            "--pool-size",
            action="store",
            type=int,
            default=3,
            help="How many thread workers assigned to pool.",
        )


# Using a custom parser to support `--tasks-num` and `--pool-size` command
# line arguments so that users can experiment with thread pool test execution.

# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="MultiTestPartsExecution",
    parser=CustomParser,
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    merge_scheduled_parts=False,
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    # Add a thread pool test execution resource to the plan of given size.
    # Also you can use process pool or remote pool instead.
    pool = ThreadPool(name="MyPool", size=plan.args.pool_size)
    plan.add_resource(pool)

    # Add a given number of similar tests to the thread pool
    # to be executed in parallel.
    for idx in range(plan.args.parts_num):
        task = Task(
            target="make_multitest",
            module="tasks",
            kwargs={"part_tuple": (idx, plan.args.parts_num)},
        )
        plan.schedule(task, resource="MyPool")


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
