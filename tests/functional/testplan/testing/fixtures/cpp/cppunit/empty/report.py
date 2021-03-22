from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="My Cppunit",
            category="cppunit",
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
                                    "type": "Attachment",
                                    "description": "Process stdout",
                                },
                                {
                                    "type": "Attachment",
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
