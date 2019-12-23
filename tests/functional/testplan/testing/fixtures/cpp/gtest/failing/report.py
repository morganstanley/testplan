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
                    category='testsuite',
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
