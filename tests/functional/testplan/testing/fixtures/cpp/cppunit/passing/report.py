from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyCppunit",
            category="cppunit",
            entries=[
                TestGroupReport(
                    name="mycppunit",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="testNotEqual",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testGreater",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testLess",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testMisc",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testOr",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testAnd",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testNot",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="testXor",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                    ],
                ),
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
        )
    ],
)
