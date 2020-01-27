#!/usr/bin/env python
"""
This example demonstrates FIX communication via FixServer and FixClient drivers.

NOTE: The FixServer driver implementation requires select.poll(), which is not
available on all platforms. Typically it is available on POSIX systems but
not on Windows. This example will not run correctly on platforms where
select.poll() is not available.
"""

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum

import over_one_session
import over_two_sessions


OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="FIXCommunication",
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
    plan.add(over_one_session.get_multitest())
    plan.add(over_two_sessions.get_multitest())


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
