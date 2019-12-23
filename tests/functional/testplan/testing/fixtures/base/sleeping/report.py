import re

from testplan.report import (
  TestReport, TestGroupReport,
  TestCaseReport, Status
)

testcase_report = TestCaseReport(
    name='failure',
    entries=[
        {
            'type': 'RawAssertion',
            'description': 'Process failure details',
            # 'content': ''
        }
    ]
)

testcase_report.status_override = Status.ERROR


my_test_report = TestGroupReport(
    name='MyTest',
    category='dummytest',
    entries=[
        TestGroupReport(
            name='ProcessFailure',
            category='testsuite',
            entries=[testcase_report]
        )
    ],
)

my_test_report.logs = [
    {'message': re.compile(
        r"RuntimeError: Timeout while"
        r" running DummyTest\[MyTest\] after 1 seconds\.")}
]


my_test_report.status_override = Status.ERROR


expected_report = TestReport(
    name='plan',
    entries=[my_test_report]
)
