#!/usr/bin/env python

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum

from my_tests.mtest import make_multitest


# Hard coding interactive mode usage.
@test_plan(name='MyPlan',
           interactive=True,
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
# When HTTP handler starts listening on <IP>:$PORT
# use a tool like curl to send HTTP requests and execute/reload tests.
#
# First execute the tests:
#     curl -X POST http://127.0.0.1:$PORT/sync/run_tests
#
# Make an an edit in my_tests/dependency.py
#   VALUE = 3
#     change to:
#   VALUE = 1
#
# Reload the code:
#     curl -X POST http://127.0.0.1:$PORT/sync/reload
#
# Re-run the tests:
#     curl -X POST http://127.0.0.1:$PORT/sync/run_tests
#
# Run only one suite:
#     curl -X POST http://127.0.0.1:$PORT/sync/run_test_suite -d '{"test_uid": "Test1", "suite_uid": "BasicSuite"}'
#
# .. and all other operations that Testplan interactive provides.


