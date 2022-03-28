from pathlib import Path

from testplan.report import TestReport, TestGroupReport, TestCaseReport
from . import ImporterTestFixture


fixture = ImporterTestFixture(
    Path(__file__).with_suffix(".xml"),
    TestReport(
        name="JUnit Result",
        description="JUnit Import",
        entries=[
            TestGroupReport(
                name="JUnit Result",
                category="junit",
                description="JUnit Import",
                entries=[
                    TestGroupReport(
                        name="FooTestCase",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="FooTestCase::One",
                                entries=[
                                    {"type": "RawAssertion", "passed": True}
                                ],
                            ),
                            TestCaseReport(
                                name="FooTestCase::Two",
                                entries=[
                                    {"type": "RawAssertion", "passed": True}
                                ],
                            ),
                        ],
                    ),
                    TestGroupReport(
                        name="BarTestCase",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="BarTestCase::One",
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
