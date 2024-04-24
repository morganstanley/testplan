import re

from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    Status,
    RuntimeStatus,
)

testcase_report = TestCaseReport(
    name="ExitCodeCheck",
    entries=[
        {
            "type": "RawAssertion",
            "description": "Process exit code check",
            "passed": False,
        },
        {"type": "Attachment", "description": "Process stdout"},
        {"type": "Attachment", "description": "Process stderr"},
    ],
)

testcase_report.runtime_status = RuntimeStatus.FINISHED

my_test_report = TestGroupReport(
    name="MyTest",
    category="unittest",
    entries=[
        TestGroupReport(
            name="Environment Start",
            category="synthesized",
            entries=[TestCaseReport(name="starting", uid="starting")],
            tags=None,
        ),
        TestGroupReport(
            name="ProcessChecks",
            category="testsuite",
            entries=[testcase_report],
        ),
        TestGroupReport(
            name="Environment Stop",
            category="synthesized",
            entries=[TestCaseReport(name="stopping", uid="stopping")],
            tags=None,
        ),
    ],
)

my_test_report.logs = [
    {
        "message": re.compile(
            r"RuntimeError: Timeout while"
            r" running DummyTest\[MyTest\] after 1 seconds\."
        )
    }
]

my_test_report.status_override = Status.ERROR

expected_report = TestReport(
    name="plan",
    entries=[
        my_test_report,
    ],
)
