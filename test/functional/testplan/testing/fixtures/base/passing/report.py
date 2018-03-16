from testplan.report.testing import TestReport, TestGroupReport

expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyTest',
            category='DummyTest',
            entries=[]
        ),
    ]
)
