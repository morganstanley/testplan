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
                )
            ],
        )
    ],
)
