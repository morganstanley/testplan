from pathlib import Path

from testplan.report import TestReport, TestGroupReport, TestCaseReport
from tests.unit.testplan.importers.fixtures import (
    ImporterTestFixture,
)

fixture = ImporterTestFixture(
    Path(__file__).with_suffix(".xml"),
    TestReport(
        name="My GTest",
        description="My GTest Import",
        entries=[
            TestGroupReport(
                name="My GTest",
                description="My GTest Import",
                category="gtest",
                entries=[
                    TestGroupReport(
                        name="SquareRootTest",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="PositiveNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": True},
                                ],
                            ),
                            TestCaseReport(
                                name="NegativeNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": True},
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
                                    {"type": "RawAssertion", "passed": True},
                                ],
                            ),
                            TestCaseReport(
                                name="NegativeNos",
                                entries=[
                                    {"type": "RawAssertion", "passed": True},
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    ),
)
