import re

from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
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

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
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
    ],
)
