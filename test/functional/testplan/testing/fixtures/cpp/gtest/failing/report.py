from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyGTest',
            category='GTest',
            entries=[
                TestGroupReport(
                    name='SquareRootTest',
                    category='suite',
                    entries=[
                        TestCaseReport(
                            name='PositiveNos',
                            entries=[
                                {
                                    'type': 'RawAssertion',
                                    'passed': False,
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='NegativeNos',
                            entries=[],
                        ),
                    ]
                ),
                TestGroupReport(
                    name='SquareRootTestNonFatal',
                    category='suite',
                    entries=[
                        TestCaseReport(
                            name='PositiveNos',
                            entries=[
                                {
                                    'type': 'RawAssertion',
                                    'passed': False,
                                },
                                {
                                    'type': 'RawAssertion',
                                    'passed': False,
                                },
                            ]
                        ),
                        TestCaseReport(
                            name='NegativeNos',
                            entries=[]
                        ),
                    ]
                ),
            ]
        ),
    ]
)
