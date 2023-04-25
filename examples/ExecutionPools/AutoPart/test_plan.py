#!/usr/bin/env python
"""
This example is to demonstrate auto-part feature in a process pool.
"""

import sys
from testplan import test_plan
from testplan.runners.pools.process import ProcessPool
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


# The auto_part_runtime_limit argument instructs testplan to split parts="auto"
# Multitest into optimal number of parts so that the runtime of each part
# is not more than the limit.
@test_plan(
    name="AutoPartExample",
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
    auto_part_runtime_limit=100,
    plan_runtime_target=100,
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    # Enable smart-schedule pool size
    pool = ProcessPool(name="MyPool", size="auto")

    # Add a process pool test execution resource to the plan of given size.
    plan.add_resource(pool)

    # Discover tasks and calculate the right size of the pool based on the weight (runtime) of the
    # tasks so that runtime of all tasks meets the plan_runtime_target.
    plan.schedule_all(
        path=".",
        name_pattern=r".*task\.py$",
        resource="MyPool",
    )


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
