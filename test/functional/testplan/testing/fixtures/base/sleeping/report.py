import re
from testplan.report.testing import TestReport, TestGroupReport, Status

my_test_report = TestGroupReport(
    name='MyTest',
    category='DummyTest',
    entries=[],
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

