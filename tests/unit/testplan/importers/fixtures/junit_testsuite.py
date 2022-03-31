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
                        name="FooCase",
                        category="testsuite",
                        entries=[
                            TestCaseReport(
                                name="FooCase::Foo",
                                entries=[
                                    {
                                        "type": "RawAssertion",
                                        "passed": True,
                                        "content": "Testcase Foo passed",
                                    }
                                ],
                            ),
                            TestCaseReport(
                                name="FooCase::Bar",
                                entries=[
                                    {
                                        "type": "RawAssertion",
                                        "passed": False,
                                        "content": "[system-err]\nSystem error body content.\n",
                                    }
                                ],
                            ),
                            TestCaseReport(
                                name="FooCase::Baz",
                                entries=[
                                    {
                                        "type": "RawAssertion",
                                        "passed": False,
                                        "content": "",
                                    }
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    ),
)
