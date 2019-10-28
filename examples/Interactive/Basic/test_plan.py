#!/usr/bin/env python

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum

from my_tests.mtest import make_multitest


# Hard coding interactive mode usage.
@test_plan(name='MyPlan',
           interactive_port=0,
           stdout_style=Style(
               passing=StyleEnum.ASSERTION_DETAIL,
               failing=StyleEnum.ASSERTION_DETAIL))
def main(plan):

    # Adding two multitests
    plan.add(make_multitest(idx='1'))
    plan.add(make_multitest(idx='2'))


if __name__ == '__main__':
    sys.exit(not main())


# INTERACTIVE MODE DEMO:
# ----------------------
#
# View the API schema at either the localhost or LAN address printed when this
# testplan script is run. The schema is interactive so can be used to try out
# the API. To run a test, set its status to "running" on a PUT update.

