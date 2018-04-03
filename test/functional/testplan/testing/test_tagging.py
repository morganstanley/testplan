import pytest

from testplan.common.utils.testing import check_report, log_propagation_disabled

from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.logger import TESTPLAN_LOGGER

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
    tags={},
    tags_index={
        'simple': {'foo', 'bar'},
        'symbol': {'aaa', 'bbb'},
        'speed': {'slow', 'fast'},
        'color': {'red', 'blue', 'yellow', 'green'},
    },
    entries=[
        TestGroupReport(
            name='AlphaSuite',
            category='suite',
            tags={'color': {'red', 'blue'}},
            tags_index={
                'color': {'red', 'blue', 'green'},
                'simple': {'foo', 'bar'},
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={
                        'color': {'red', 'blue'},
                    },
                ),
                TestCaseReport(
                    name='test_method_1',
                    tags={
                        'simple': {'foo', 'bar'},
                    },
                    tags_index={
                        'color': {'red', 'blue'},
                    },
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={
                        'color': {'green'},
                    },
                    tags_index={
                        'color': {'red', 'blue', 'green'}
                    }
                ),
            ]
        ),
        TestGroupReport(
            name='BetaSuite',
            category='suite',
            tags={'color': {'yellow'}},
            tags_index={
                'color': {'yellow', 'red'},
                'simple': {'foo'}
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={
                        'color': {'yellow'},
                    },
                ),
                TestCaseReport(
                    name='test_method_1',
                    tags={
                        'simple': {'foo'},
                    },
                    tags_index={
                        'color': {'yellow'},
                        'simple': {'foo'}
                    },
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={
                        'color': {'red'},
                    },
                    tags_index={
                        'color': {'yellow', 'red'},
                    },
                ),
            ],
        ),
        TestGroupReport(
            name='GammaSuite',
            category='suite',
            tags={},
            tags_index={
                'symbol': {'aaa', 'bbb'},
                'speed': {'slow', 'fast'}
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={},
                ),
                TestGroupReport(
                    name='test_param',
                    category='parametrization',
                    tags={
                        'speed': {'slow'},
                    },
                    tags_index={
                        'speed': {'slow'},
                        'symbol': {'aaa', 'bbb'},
                    },
                    entries=[
                        TestCaseReport(
                            name='test_param__value_AAA',
                            tags={
                                'symbol': {'aaa'},
                            },
                            tags_index={
                                'speed': {'slow'},
                                'symbol': {'aaa'},
                            }
                        ),
                        TestCaseReport(
                            name='test_param__value_BBB',
                            tags={
                                'symbol': {'bbb'},
                            },
                            tags_index={
                                'speed': {'slow'},
                                'symbol': {'bbb'},
                            }
                        ),
                    ]
                ),
                TestGroupReport(
                    name='test_param_2',
                    category='parametrization',
                    tags={
                        'speed': {'fast'},
                    },
                    tags_index={
                        'speed': {'fast'},
                    },
                    entries=[
                        TestCaseReport(
                            name='test_param_2__value_XXX',
                            tags={},
                            tags_index={
                                'speed': {'fast'},
                            }
                        ),
                        TestCaseReport(
                            name='test_param_2__value_YYY',
                            tags={},
                            tags_index={
                                'speed': {'fast'},
                            }
                        ),
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
    tags_index={
        'simple': {'foo', 'bar'},
        'symbol': {'aaa', 'bbb'},
        'speed': {'slow', 'fast'},
        'color': {'orange', 'red', 'blue', 'yellow', 'green'},
        'environment': {'server'}
    },
    entries=[
        TestGroupReport(
            name='AlphaSuite',
            category='suite',
            tags={'color': {'red', 'blue'}},
            tags_index={
                'color': {'red', 'blue', 'orange', 'green'},
                'simple': {'foo', 'bar'},
                'environment': {'server'}
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={
                        'color': {'red', 'blue', 'orange'},
                        'environment': {'server'}
                    },
                ),
                TestCaseReport(
                    name='test_method_1',
                    tags={
                        'simple': {'foo', 'bar'},
                    },
                    tags_index={
                        'color': {'red', 'blue', 'orange'},
                        'environment': {'server'}
                    },
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={
                        'color': {'green'},
                    },
                    tags_index={
                        'environment': {'server'},
                        'color': {'red', 'blue', 'orange', 'green'}}
                ),
            ]
        ),
        TestGroupReport(
            name='BetaSuite',
            category='suite',
            tags={'color': {'yellow'}},
            tags_index={
                'color': {'yellow', 'orange', 'red'},
                'environment': {'server'},
                'simple': {'foo'}
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={
                        'color': {'yellow', 'orange'},
                        'environment': {'server'},
                    },
                ),
                TestCaseReport(
                    name='test_method_1',
                    tags={
                        'simple': {'foo'},
                    },
                    tags_index={
                        'color': {'yellow', 'orange'},
                        'environment': {'server'},
                        'simple': {'foo'}
                    },
                ),
                TestCaseReport(
                    name='test_method_2',
                    tags={
                        'color': {'red'},
                    },
                    tags_index={
                        'color': {'yellow', 'orange', 'red'},
                        'environment': {'server'},
                    },
                ),
            ]
        ),
        TestGroupReport(
            name='GammaSuite',
            category='suite',
            tags={},
            tags_index={
                'color': {'orange'},
                'environment': {'server'},
                'symbol': {'aaa', 'bbb'},
                'speed': {'slow', 'fast'}
            },
            entries=[
                TestCaseReport(
                    name='test_method_0',
                    tags={},
                    tags_index={
                        'color': {'orange'},
                        'environment': {'server'},
                    },
                ),
                TestGroupReport(
                    name='test_param',
                    category='parametrization',
                    tags={
                        'speed': {'slow'},
                    },
                    tags_index={
                        'speed': {'slow'},
                        'symbol': {'aaa', 'bbb'},
                        'color': {'orange'},
                        'environment': {'server'},
                    },
                    entries=[
                        TestCaseReport(
                            name='test_param__value_AAA',
                            tags={
                                'symbol': {'aaa'},
                            },
                            tags_index={
                                'speed': {'slow'},
                                'symbol': {'aaa'},
                                'color': {'orange'},
                                'environment': {'server'},
                            }
                        ),
                        TestCaseReport(
                            name='test_param__value_BBB',
                            tags={
                                'symbol': {'bbb'},
                            },
                            tags_index={
                                'speed': {'slow'},
                                'symbol': {'bbb'},
                                'color': {'orange'},
                                'environment': {'server'},
                            }
                        ),
                    ]
                ),
                TestGroupReport(
                    name='test_param_2',
                    category='parametrization',
                    tags={
                        'speed': {'fast'},
                    },
                    tags_index={
                        'speed': {'fast'},
                        'color': {'orange'},
                    },
                    entries=[
                        TestCaseReport(
                            name='test_param_2__value_XXX',
                            tags={},
                            tags_index={
                                'speed': {'fast'},
                                'color': {'orange'},
                            }
                        ),
                        TestCaseReport(
                            name='test_param_2__value_YYY',
                            tags={},
                            tags_index={
                                'speed': {'fast'},
                                'color': {'orange'},
                            }
                        ),
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
