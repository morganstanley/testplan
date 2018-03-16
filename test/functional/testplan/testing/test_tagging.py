from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.testing import tagging


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


def test_multitest_tagging():

    multitest = MultiTest(
        name='MyMultitest', suites=[AlphaSuite(), BetaSuite()])

    assert tagging.get_test_tags(multitest) == {
        'color': frozenset({'blue', 'yellow', 'red', 'green'}),
        'simple': frozenset({'bar', 'foo'})
    }

    assert tagging.get_suite_tags(AlphaSuite()) == {
        'color': frozenset({'blue', 'red', 'green'}),
        'simple': frozenset({'bar', 'foo'})
    }

    assert tagging.get_suite_tags(BetaSuite) == {
        'color': frozenset({'yellow', 'red'}),
        'simple': frozenset({'foo'})
    }

    plan = Testplan(name='plan', parse_cmdline=False)
    plan.add(multitest)

    plan.run()

    test_report = plan.report
    multitest_report = test_report[0]
    suite_report_a, suite_report_b = multitest_report

    assert test_report.tags_index == {
        'color': frozenset({'green', 'red', 'blue', 'yellow'}),
        'simple': frozenset({'foo', 'bar'})
    }

    assert suite_report_a.tags == {'color': frozenset({'red', 'blue'})}
    assert suite_report_a.tags_index == {
        'color': frozenset({'red', 'blue', 'green'}),
        'simple': frozenset({'foo', 'bar'})
    }

    assert suite_report_b.tags == {'color': frozenset({'yellow'})}
    assert suite_report_b.tags_index == {
        'color': frozenset({'yellow', 'red'}),
        'simple': frozenset({'foo'})
    }

    tc_report_a_0, tc_report_a_1, tc_report_a_2 = suite_report_a
    tc_report_b_0, tc_report_b_1, tc_report_b_2 = suite_report_b

    assert tc_report_a_0.tags == {}
    assert tc_report_a_0.tags_index == {'color': frozenset({'red', 'blue'})}

    assert tc_report_a_1.tags == {'simple': frozenset({'foo', 'bar'})}
    assert tc_report_a_1.tags_index == {
        'simple': frozenset({'foo', 'bar'}),
        'color': frozenset({'red', 'blue'})
    }

    assert tc_report_a_2.tags == {'color': frozenset({'green'})}
    assert tc_report_a_2.tags_index == {
        'color': frozenset({'red', 'blue', 'green'})
    }

    assert tc_report_b_0.tags == {}
    assert tc_report_b_0.tags_index == {'color': frozenset({'yellow'})}

    assert tc_report_b_1.tags == {'simple': frozenset({'foo'})}
    assert tc_report_b_1.tags_index == {
        'simple': frozenset({'foo'}),
        'color': frozenset({'yellow'})
    }

    assert tc_report_b_2.tags == {'color': frozenset({'red'})}
    assert tc_report_b_2.tags_index == {'color': frozenset({'yellow', 'red'})}
