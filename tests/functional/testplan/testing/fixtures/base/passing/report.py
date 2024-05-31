from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    TestCaseReport,
    TestGroupReport,
    TestReport,
)

testcase_report = TestCaseReport(
    name="ExitCodeCheck",
    category=ReportCategories.SYNTHESIZED,
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


expected_report_with_driver = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyTest",
            category="dummytest",
            entries=[
                TestGroupReport(
                    name="Environment Start",
                    category="synthesized",
                    entries=[
                        TestCaseReport(
                            name="Starting",
                            uid="Starting",
                            description="",
                            entries=[
                                {
                                    "type": "Log",
                                    "description": "MyDriver[My executable] Status: STARTED",
                                },
                            ],
                        )
                    ],
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
                    entries=[
                        TestCaseReport(
                            name="Stopping",
                            uid="Stopping",
                            description="",
                            entries=[],
                        )
                    ],
                    tags=None,
                ),
            ],
        ),
    ],
)
