"""
Test Matplotlib Assertion - separate to ensure test is skippable on windows.
"""
import re

from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport

from testplan.testing.multitest.base import Categories

expected_report = TestReport(
    name='plan',
    entries=[
        TestGroupReport(
            name='MyMultitest',
            category=Categories.MULTITEST,
            entries=[
                TestGroupReport(
                    name='MySuite',
                    category=Categories.SUITE,
                    entries=[
                        TestCaseReport(
                            name='test_matplot',
                            entries=[
                                {
                                    'image_file_path': re.compile('^.+\.png$'),
                                    'width': 2.0,
                                    'height': 2.0,
                                    'type': 'MatPlot',
                                    'description': 'My matplot'
                                }
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)
