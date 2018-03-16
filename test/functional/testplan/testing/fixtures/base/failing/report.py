import re
from testplan.report.testing import TestReport, TestGroupReport, Status

my_test_report = TestGroupReport(
    name='MyTest',
    category='DummyTest',
    entries=[],
)

my_test_report.status_override = Status.ERROR

my_test_report.logs = [
    {'message': re.compile(
        r'RuntimeError: Test process of'
        r' DummyTest\[MyTest\] exited with nonzero status: 5\.')
    }
]

expected_report = TestReport(
    name='plan',
    entries=[my_test_report]
)

