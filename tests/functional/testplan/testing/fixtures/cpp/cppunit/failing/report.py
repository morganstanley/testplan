from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="My Cppunit",
            category="cppunit",
            entries=[
                TestGroupReport(
                    name="All Tests",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="Comparison::testEqual",
                            entries=[
                                {"type": "RawAssertion", "passed": False}
                            ],
                        ),
                        TestCaseReport(
                            name="LogicalOp::testAnd",
                            entries=[
                                {"type": "RawAssertion", "passed": False}
                            ],
                        ),
                        TestCaseReport(
                            name="Comparison::testGreater",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="Comparison::testLess",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="Comparison::testMisc",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="LogicalOp::testOr",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="LogicalOp::testNot",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                        TestCaseReport(
                            name="LogicalOp::testXor",
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
                                {"type": "RawAssertion", "passed": False},
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
        )
    ],
)
