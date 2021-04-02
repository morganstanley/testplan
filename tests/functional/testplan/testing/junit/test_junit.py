"""Unit tests for the JUnit test runner."""
import os

import pytest

import testplan.report
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing import junit
from testplan.report import TestReport, TestGroupReport, TestCaseReport
from testplan.common.utils.testing import (
    log_propagation_disabled,
    check_report,
)
from pytest_test_filters import skip_on_windows

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
JUNIT_FAKE_BIN = os.path.join(CURRENT_PATH, "junit_mock.py")
REPORT_PATH = os.path.join(CURRENT_PATH, "build", "test-results", "test")


expect_report = TestGroupReport(
    name="My Junit",
    category="junit",
    description="Junit example test",
    entries=[
        TestGroupReport(
            name="com.gradle.example.application.ApplicationTests",
            category="testsuite",
            entries=[
                TestCaseReport(
                    name="contextLoads()",
                    entries=[
                        {
                            "content": "Testcase contextLoads() passed",
                            "flag": "DEFAULT",
                            "passed": True,
                            "description": "Passed",
                            "meta_type": "assertion",
                            "type": "RawAssertion",
                            "category": "DEFAULT",
                            "line_no": None,
                        }
                    ],
                )
            ],
            tags=None,
        ),
        TestGroupReport(
            name="com.gradle.example.application.MessageServiceTest",
            category="testsuite",
            entries=[
                TestCaseReport(
                    name="testGet()",
                    entries=[
                        {
                            "flag": "DEFAULT",
                            "passed": False,
                            "meta_type": "assertion",
                            "type": "Fail",
                            "category": "DEFAULT",
                            "line_no": None,
                        },
                        {
                            "flag": "DEFAULT",
                            "language": "java",
                            "description": "stacktrace",
                            "meta_type": "entry",
                            "type": "CodeLog",
                            "category": "DEFAULT",
                            "line_no": None,
                        },
                    ],
                )
            ],
            tags=None,
        ),
        TestGroupReport(
            name="ProcessChecks",
            category="testsuite",
            entries=[
                TestCaseReport(
                    name="ExitCodeCheck",
                    entries=[
                        {
                            "flag": "DEFAULT",
                            "passed": True,
                            "description": "Process exit code check",
                            "meta_type": "assertion",
                            "type": "RawAssertion",
                            "category": "DEFAULT",
                            "line_no": None,
                        },
                        {
                            "flag": "DEFAULT",
                            "description": "Process stdout",
                            "meta_type": "entry",
                            "type": "Attachment",
                            "category": "DEFAULT",
                            "line_no": None,
                        },
                        {
                            "flag": "DEFAULT",
                            "description": "Process stderr",
                            "meta_type": "entry",
                            "type": "Attachment",
                            "category": "DEFAULT",
                            "line_no": None,
                        },
                    ],
                )
            ],
            tags=None,
        ),
    ],
    tags=None,
)


@skip_on_windows(reason="JUnit is skipped on Windows.")
def test_run_test(mockplan):
    mockplan.add(
        junit.JUnit(
            name="My Junit",
            description="Junit example test",
            binary=JUNIT_FAKE_BIN,
            junit_args=["test"],
            results_dir=REPORT_PATH,
            proc_cwd=CURRENT_PATH,
        )
    )

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert mockplan.run().run is True

    report = mockplan.report
    assert report.status == testplan.report.Status.FAILED
    mt_report = report.entries[0]
    assert len(mt_report.entries) == 3

    check_report(expect_report, mt_report)
