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


expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyTest',
            category='dummytest',
            entries=[
                TestGroupReport(
                    name='ProcessFailure',
                    category='testsuite',
                    entries=[testcase_report]
                )
            ]
        )
    ]
)
