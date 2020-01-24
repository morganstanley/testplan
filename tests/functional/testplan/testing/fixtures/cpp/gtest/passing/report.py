from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyGTest',
            category='gtest',
            entries=[
                TestGroupReport(
                    name='SquareRootTest',
                    category='testsuite',
                    entries=[
                        TestCaseReport(
                            name='PositiveNos',
                            status_override = 'passed',
                            entries=[]
                        ),
                        TestCaseReport(
                            name='NegativeNos',
                            status_override = 'passed',
                            entries=[],
                        ),
                    ]
                ),
                TestGroupReport(
                    name='SquareRootTestNonFatal',
                    category='testsuite',
                    entries=[
                        TestCaseReport(
                            name='PositiveNos',
                            status_override = 'passed',
                            entries=[]
                        ),
                        TestCaseReport(
                            name='NegativeNos',
                            status_override = 'passed',
                            entries=[]
                        ),
                    ]
                ),
            ]
        ),
    ]
)
