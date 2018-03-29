#!/usr/bin/env python
"""
This example is to demonstrate HTTP communication test scenarios.
"""

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum

import http_basic
import http_custom_handler

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(name='HTTPConnections',
           pdf_path='report.pdf',
           stdout_style=OUTPUT_STYLE,
           pdf_style=OUTPUT_STYLE)
def main(plan):
    """
    Testplan decorated main function to add and execute 2 MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    plan.add(http_basic.get_multitest('HTTPBasic'))
    plan.add(http_custom_handler.get_multitest('HTTPCustomHandler'))


if __name__ == '__main__':
    res = main()
    print('Exiting code: {}'.format(res.exit_code))
    sys.exit(res.exit_code)
