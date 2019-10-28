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
# You can browse the API schema at either localhost or at the LAN address
# that's printed when running this testplan script. The API schema is
# interactive so you can test out the available functionality. In order to
# run a test, issue a PUT request with the test's status set to "running".
