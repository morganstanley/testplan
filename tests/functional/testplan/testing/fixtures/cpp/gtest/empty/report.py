from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyGTest",
            category="gtest",
            tags=None,
            entries=[
                TestGroupReport(
                    name="ProcessChecks",
                    category="testsuite",
                    entries=[
                        TestCaseReport(
                            name="ExitCodeCheck",
                            entries=[{"type": "RawAssertion", "passed": True}],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
