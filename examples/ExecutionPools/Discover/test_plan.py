#!/usr/bin/env python
"""
Discover and schedule tasks that spread across the project for parallel execution in Pool.
"""

import sys

from testplan import test_plan
from testplan.runners.pools.process import ProcessPool
from testplan.report.testing.styles import Style, StyleEnum


OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
@test_plan(
    name="TaskDiscovery",
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    merge_scheduled_parts=True,
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    # Add a process pool test execution resource to the plan of given size.
    # Also you can use thread pool or remote pool instead.
    pool = ProcessPool(name="MyPool")
    plan.add_resource(pool)

    # Create task objects from all @task_target we could find in the modules
    # that matches the name pattern under the specified path, and schedule them
    # to MyPool.

    plan.schedule_all(
        path=".", name_pattern=r".*tasks\.py$", resource="MyPool"
    )


if __name__ == "__main__":
    res = main()
    if res.report.entries:
        assert len(res.report.entries) == 5
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
