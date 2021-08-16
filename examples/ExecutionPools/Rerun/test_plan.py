#!/usr/bin/env python
"""
This example is to demonstrate task level rerun feature in a pool.
"""

import os
import sys
import uuid
import getpass
import tempfile

from testplan import test_plan
from testplan import Task
from testplan.runners.pools.base import Pool as ThreadPool

from testplan.parser import TestplanParser
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


class CustomParser(TestplanParser):
    """Inheriting base parser."""

    def add_arguments(self, parser):
        """Defining custom arguments for this Testplan."""
        parser.add_argument("--pool-size", action="store", type=int, default=4)


# Using a custom parser to support `--tasks-num` and `--pool-size` command
# line arguments so that users can experiment with process pool test execution.

# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="PoolExecutionAndTaskRerun",
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
    # Add a thread pool test execution resource to the plan of given size.
    # Can also use a process pool instead.
    pool = ThreadPool(name="MyPool", size=plan.args.pool_size)
    plan.add_resource(pool)

    # Add a task with `rerun` argument to the thread pool
    tmp_file = os.path.join(
        tempfile.gettempdir(), getpass.getuser(), "{}.tmp".format(uuid.uuid4())
    )
    task = Task(
        target="make_multitest", module="tasks", args=(tmp_file,), rerun=2
    )
    plan.schedule(task, resource="MyPool")


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
