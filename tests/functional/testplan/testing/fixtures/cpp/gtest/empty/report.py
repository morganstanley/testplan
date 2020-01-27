from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyGTest", category="gtest", entries=[], tags=None
        )
    ],
)
