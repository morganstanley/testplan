from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="My GTest",
            category="gtest",
            entries=[
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="ExitCodeCheck",
                            entries=[
                                {"type": "RawAssertion", "passed": True},
                                {
                                    "type": "Log",
                                    "description": "Process stdout",
                                },
                                {
                                    "type": "Log",
                                    "description": "Process stderr",
                                },
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
