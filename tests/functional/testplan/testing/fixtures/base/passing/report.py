from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    RuntimeStatus,
)
from testplan.testing.multitest.entries.assertions import RawAssertion

testcase_report = TestCaseReport(
    name="ExitCodeCheck",
    uid="ExitCodeCheck",
    suite_related=True,
    entries=[
        {
            "type": "RawAssertion",
            "description": "Process exit code check",
            "passed": True,
        },
        {"type": "Attachment", "description": "Process stdout"},
        {"type": "Attachment", "description": "Process stderr"},
    ],
)

testcase_report.runtime_status = RuntimeStatus.FINISHED

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="dummytest",
            entries=[
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[testcase_report],
                ),
            ],
        ),
    ],
)
