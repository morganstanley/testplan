"""
Test Matplotlib Assertion - separate to ensure test is skippable on windows.
"""
import re

from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
)

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyMultitest",
            category=ReportCategories.MULTITEST,
            entries=[
                TestGroupReport(
                    name="Environment Start",
                    category="synthesized",
                    entries=[TestCaseReport(name="starting", uid="starting")],
                    tags=None,
                ),
                TestGroupReport(
                    name="MySuite",
                    category=ReportCategories.TESTSUITE,
                    entries=[
                        TestCaseReport(
                            name="test_matplot",
                            entries=[
                                {
                                    "source_path": re.compile(r"^.+\.png$"),
                                    "type": "MatPlot",
                                    "description": "My matplot",
                                }
                            ],
                        )
                    ],
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
