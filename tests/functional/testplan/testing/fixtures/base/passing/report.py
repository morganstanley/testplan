from testplan.report import TestReport, TestGroupReport

expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyTest',
            category='dummytest',
            entries=[]
        ),
    ]
)
