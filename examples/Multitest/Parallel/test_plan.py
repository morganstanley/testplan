#!/usr/bin/env python
"""
Example script to demonstrate parallel test execution of a MultiTest.
"""
import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


@test_plan(
    name="ParallelMultiTest",
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
)
def main(plan):
    """
    Testplan decorated main function. Adds a single parallel MultiTest to the
    test plan.

    :param plan: Plan to add MultiTest to.
    :return: Results of tests.
    """
    plan.schedule(target="make_multitest", module="parallel_tasks")


if __name__ == "__main__":
    sys.exit(main().exit_code)
