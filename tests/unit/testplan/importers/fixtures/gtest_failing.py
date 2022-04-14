from pathlib import Path

from testplan.report import TestReport, TestGroupReport, TestCaseReport
from . import ImporterTestFixture


fixture = ImporterTestFixture(
    Path(__file__).with_suffix(".xml"),
    TestReport(
        name="My GTest",
        description="My GTest Import",
        entries=[
            TestGroupReport(
                name="My GTest",
                category="gtest",
                description="My GTest Import",
                entries=[
                    TestGroupReport(
                        name="SquareRootTest",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="PositiveNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": False}
                                ],
                            ),
                            TestCaseReport(
                                name="NegativeNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": True}
                                ],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="SquareRootTestNonFatal",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="PositiveNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": False},
                                    {"type": "RawAssertion", "passed": False},
                                ],
                            ),
                            TestCaseReport(
                                name="NegativeNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": True}
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    ),
)
