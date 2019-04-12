import re

from testplan.report.testing import (
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
                    category='suite',
                    entries=[testcase_report]
                )
            ]
        )
    ]
)
