from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys
import atexit
import re

with open('testplan_path.txt', 'r') as fobj:
    sys.path.append(fobj.read().strip(os.linesep))
atexit.register(os.remove, 'testplan_path.txt')

from testplan import Testplan
from testplan.testing.multitest import MultiTest

from testplan.common.utils.comparison import compare


PASSED_CASE_REPORT =\
    {'type': 'Equal', 'label': '==', 'meta_type': 'assertion',
     'category': 'DEFAULT', 'machine_time':  re.compile('\d+\.?\d*'),
     'line_no': 7, 'passed': True, 'first': 1, 'second': 1,
     'description': 'Assertion', 'utc_time':  re.compile('\d+\.?\d*')}

FAILED_CASE_REPORT =\
    {'type': 'Equal', 'label': '==', 'meta_type': 'assertion',
     'category': 'DEFAULT', 'machine_time':  re.compile('\d+\.?\d*'),
     'line_no': 7, 'passed': False, 'first': 1, 'second': 3,
     'description': 'Assertion', 'utc_time':  re.compile('\d+\.?\d*')}


def main():
    # CREATE AN INTERACTIVE TESTPLAN
    plan = Testplan(name='MyPlan', interactive=True, interactive_block=False)

    with open('basic_suite_template.txt') as fobj:
        template = fobj.read()

    # WRITE A FAILING TESTCASE
    with open('basic_suite_with_value.py', 'w') as fobj:
        fobj.write(template.format(VALUE=3))
    atexit.register(os.remove, 'basic_suite_with_value.py')

    from basic_suite_with_value import SuiteTemplate

    # TRIGGER RUN OF INTERACTIVE EXECUTIONER
    plan.run()

    # ADD A TEST
    plan.add(MultiTest(
        name='Test1',
        suites=[SuiteTemplate()]))

    # RUN THE TESTS
    plan.i.run_tests()

    # EXPECTED 1 != 3 FAILURE
    serialized = plan.i.test_case_report(
        test_uid='Test1', suite_uid='SuiteTemplate', case_uid='basic_case',
        serialized=True)
    assert compare(
         serialized['entries'][0]['entries'][0]['entries'][0],
         FAILED_CASE_REPORT)[0] is True
    assert plan.i.report().passed is False

    # APPLY A CODE CHANGE - FIX
    with open('basic_suite_with_value.py', 'w') as fobj:
        fobj.write(template.format(VALUE=1))

    # SEND RELOAD CODE
    plan.i.reload()

    # RUN TESTS AGAIN
    plan.i.run_tests()

    # EXPECTED 1 == 1 SUCCESS
    serialized = plan.i.test_case_report(
        test_uid='Test1', suite_uid='SuiteTemplate', case_uid='basic_case',
        serialized=True)
    assert compare(
        serialized['entries'][0]['entries'][0]['entries'][0],
        PASSED_CASE_REPORT)[0] is True
    assert plan.i.report().passed is True


if __name__ == "__main__":
    main()
