import pytest

from testplan.common.utils.testing import check_report, log_propagation_disabled

from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.logger import TESTPLAN_LOGGER

from testplan import Testplan


@testsuite(tags={'color': ['red', 'blue']})
class AlphaSuite(object):

    @testcase
    def test_method_0(self, env, result):
        pass

    @testcase(tags=('foo', 'bar'))
    def test_method_1(self, env, result):
        pass

    @testcase(tags={'color': 'green'})
    def test_method_2(self, env, result):
        pass


@testsuite(tags={'color': 'yellow'})
class BetaSuite(object):

    @testcase
    def test_method_0(self, env, result):
        pass

    @testcase(tags='foo')
    def test_method_1(self, env, result):
        pass

    @testcase(tags={'color': 'red'})
    def test_method_2(self, env, result):
        pass


@testsuite
class GammaSuite(object):

    @testcase
    def test_method_0(self, env, result):
        pass

    @testcase(
        parameters=('AAA', 'BBB'),
        tag_func=lambda kwargs: {'symbol': kwargs['value'].lower()},
        tags={'speed': 'slow'},
    )
    def test_param(self, env, result, value):
        pass

    @testcase(
        parameters=('XXX', 'YYY'),
        tags={'speed': 'fast'}
    )
    def test_param_2(self, env, result, value):
        pass


report_for_multitest_without_tags = TestGroupReport(
    name='MyMultitest',
    category='multitest',
    entries=[
        TestGroupReport(
            name='AlphaSuite',
            category='suite',
            tags={'color': {'red', 'blue'}},
            entries=[
                TestCaseReport(name='test_method_0'),
                TestCaseReport(
                    name='test_method_1',
                    tags={'simple': {'foo', 'bar'}},
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={'color': {'green'}},
                ),
            ]
        ),
        TestGroupReport(
            name='BetaSuite',
            category='suite',
            tags={'color': {'yellow'}},
            entries=[
                TestCaseReport(name='test_method_0'),
                TestCaseReport(
                    name='test_method_1',
                    tags={'simple': {'foo'}},
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={'color': {'red'}},
                ),
            ],
        ),
        TestGroupReport(
            name='GammaSuite',
            category='suite',
            entries=[
                TestCaseReport(name='test_method_0'),
                TestGroupReport(
                    name='test_param',
                    category='parametrization',
                    tags={'speed': {'slow'}},
                    entries=[
                        TestCaseReport(
                            name='test_param__value_AAA',
                            tags={'symbol': {'aaa'}},
                        ),
                        TestCaseReport(
                            name='test_param__value_BBB',
                            tags={'symbol': {'bbb'}},
                        ),
                    ]
                ),
                TestGroupReport(
                    name='test_param_2',
                    category='parametrization',
                    tags={'speed': {'fast'}},
                    entries=[
                        TestCaseReport(name='test_param_2__value_XXX'),
                        TestCaseReport(name='test_param_2__value_YYY'),
                    ]
                )
            ]
        )
    ]
)


report_for_multitest_with_tags = TestGroupReport(
    name='MyMultitest',
    category='multitest',
    tags={
        'color': {'orange'},
        'environment': {'server'}
    },
    entries=[
        TestGroupReport(
            name='AlphaSuite',
            category='suite',
            tags={'color': {'red', 'blue'}},
            entries=[
                TestCaseReport(name='test_method_0'),
                TestCaseReport(
                    name='test_method_1',
                    tags={'simple': {'foo', 'bar'}},
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={'color': {'green'}},
                ),
            ]
        ),
        TestGroupReport(
            name='BetaSuite',
            category='suite',
            tags={'color': {'yellow'}},
            entries=[
                TestCaseReport(name='test_method_0'),
                TestCaseReport(
                    name='test_method_1',
                    tags={'simple': {'foo'}},
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={'color': {'red'}},
                ),
            ]
        ),
        TestGroupReport(
            name='GammaSuite',
            category='suite',
            entries=[
                TestCaseReport(name='test_method_0'),
                TestGroupReport(
                    name='test_param',
                    category='parametrization',
                    tags={'speed': {'slow'}},
                    entries=[
                        TestCaseReport(
                            name='test_param__value_AAA',
                            tags={'symbol': {'aaa'}},
                        ),
                        TestCaseReport(
                            name='test_param__value_BBB',
                            tags={'symbol': {'bbb'}},
                        ),
                    ]
                ),
                TestGroupReport(
                    name='test_param_2',
                    category='parametrization',
                    tags={'speed': {'fast'}},
                    entries=[
                        TestCaseReport(name='test_param_2__value_XXX'),
                        TestCaseReport(name='test_param_2__value_YYY'),
                    ]
                )
            ]
        )
    ]
)


@pytest.mark.parametrize(
    'multitest_tags,expected_report',
    (
        ({}, report_for_multitest_without_tags),
        (
            {'color': 'orange', 'environment': 'server'},
            report_for_multitest_with_tags
        ),
    )
)
def test_multitest_tagging(multitest_tags, expected_report):

    multitest = MultiTest(
        name='MyMultitest',
        suites=[AlphaSuite(), BetaSuite(), GammaSuite()],
        tags=multitest_tags
    )

    plan = Testplan(name='plan', parse_cmdline=False)
    plan.add(multitest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan.run()

    check_report(
        expected=TestReport(
            name='plan',
            entries=[expected_report]
        ),
        actual=plan.report
    )
