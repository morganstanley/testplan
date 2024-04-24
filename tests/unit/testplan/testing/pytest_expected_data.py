"""Expected test report data used in test_pytest.py test module."""

import testplan.report


EXPECTED_DRY_RUN_REPORT = testplan.report.TestGroupReport(
    name="My PyTest",
    description="PyTest example test",
    uid="My PyTest",
    category="pytest",
    entries=[
        testplan.report.TestGroupReport(
            name="Environment Start",
            category="synthesized",
            entries=[
                testplan.report.TestCaseReport(name="starting", uid="starting")
            ],
            tags=None,
        ),
        testplan.report.TestGroupReport(
            name="pytest_tests.py::TestPytestBasics",
            uid="pytest_tests.py::TestPytestBasics",
            category="testsuite",
            entries=[
                testplan.report.TestCaseReport(
                    name="test_success", uid="test_success"
                ),
                testplan.report.TestCaseReport(
                    name="test_failure", uid="test_failure"
                ),
                testplan.report.TestGroupReport(
                    name="test_parametrization",
                    uid="test_parametrization",
                    category="parametrization",
                    entries=[
                        testplan.report.TestCaseReport(
                            name="test_parametrization[1-2-3]",
                            uid="test_parametrization[1-2-3]",
                        ),
                        testplan.report.TestCaseReport(
                            name="test_parametrization[-1--2--3]",
                            uid="test_parametrization[-1--2--3]",
                        ),
                        testplan.report.TestCaseReport(
                            name="test_parametrization[0-0-0]",
                            uid="test_parametrization[0-0-0]",
                        ),
                    ],
                ),
            ],
        ),
        testplan.report.TestGroupReport(
            name="pytest_tests.py::TestWithDrivers",
            uid="pytest_tests.py::TestWithDrivers",
            category="testsuite",
            entries=[
                testplan.report.TestCaseReport(
                    name="test_drivers", uid="test_drivers"
                )
            ],
        ),
        testplan.report.TestGroupReport(
            name="pytest_tests.py::TestWithAttachments",
            uid="pytest_tests.py::TestWithAttachments",
            category="testsuite",
            entries=[
                testplan.report.TestCaseReport(
                    name="test_attachment", uid="test_attachment"
                )
            ],
        ),
        testplan.report.TestGroupReport(
            name="pytest_tests.py::TestPytestMarks",
            uid="pytest_tests.py::TestPytestMarks",
            category="testsuite",
            entries=[
                testplan.report.TestCaseReport(
                    name="test_skipped", uid="test_skipped"
                ),
                testplan.report.TestCaseReport(
                    name="test_skipif", uid="test_skipif"
                ),
                testplan.report.TestCaseReport(
                    name="test_xfail", uid="test_xfail"
                ),
                testplan.report.TestCaseReport(
                    name="test_unexpected_error", uid="test_unexpected_error"
                ),
                testplan.report.TestCaseReport(
                    name="test_xpass", uid="test_xpass"
                ),
                testplan.report.TestCaseReport(
                    name="test_xpass_strict", uid="test_xpass_strict"
                ),
            ],
        ),
        testplan.report.TestGroupReport(
            name="Environment Stop",
            category="synthesized",
            entries=[
                testplan.report.TestCaseReport(name="stopping", uid="stopping")
            ],
            tags=None,
        ),
    ],
)
