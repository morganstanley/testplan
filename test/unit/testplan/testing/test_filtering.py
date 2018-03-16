import pytest

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan.testing import filtering


@testsuite(tags='foo')
class Alpha(object):

    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={'color': 'red'})
    def test_two(self, env, result):
        pass

    @testcase(tags={'color': 'blue'})
    def test_three(self, env, result):
        pass


@testsuite(tags='bar')
class Beta(object):

    def suite_name(self):
        return 'Custom'

    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={'color': 'blue', 'speed': 'slow'})
    def test_two(self, env, result):
        pass

    @testcase(tags={'color': 'yellow', 'speed': 'fast'})
    def test_three(self, env, result):
        pass


@testsuite(tags=('foo', 'baz'))
class Gamma(object):

    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={'speed': 'fast'})
    def test_two(self, env, result):
        pass

    @testcase(tags={'color': 'green'})
    def test_three(self, env, result):
        pass

    @testcase(tags={'color': ('blue', 'red')})
    def test_four(self, env, result):
        pass


multitest_A = MultiTest(name='AAA', suites=[Alpha()])
multitest_B = MultiTest(name='BBB', suites=[Beta()])
multitest_C = MultiTest(name='CCC', suites=[Gamma()])
multitest_D = MultiTest(name='DDD', suites=[Alpha(), Beta()])
multitest_E = MultiTest(name='EEE', suites=[Beta(), Gamma()])
multitest_F = MultiTest(name='FFF', suites=[Alpha(), Beta(), Gamma()])


class TestTags(object):

    @pytest.mark.parametrize(
        'tags, multitest, expected',
        (
            ('foo', multitest_A, True),
            (('foo', 'something', 'else'), multitest_A, True),
            ('bar', multitest_A, False),
            ({'color': 'blue'}, multitest_A, True),
            (('bar', 'baz'), multitest_F, True),
            (
                {'color': 'yellow', 'simple': 'bar', 'speed': 'slow'},
                multitest_F, True
            ),
            (
                {'color': 'orange', 'simple': 'bat', 'speed': 'medium'},
                multitest_F, False
            )
        )
    )
    def test_filter_instance(self, tags, multitest, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_instance(multitest)) == expected

    @pytest.mark.parametrize(
        'tags, testsuite_obj, expected',
        (
            ('foo', Alpha(), True),
            (('foo', 'something', 'else'), Alpha(), True),
            ('bar', Alpha(), False),
            ({'color': ('blue', 'yellow')}, Alpha(), True),
            ({'color': ('blue', 'yellow')}, Beta(), True),
            ({'color': 'blue'}, Alpha(), True),
            (('bar', 'baz'), Gamma(), True),
            (
                {'color': 'yellow', 'simple': 'bar', 'speed': 'slow'},
                Gamma(), False
            ),
        )
    )
    def test_filter_testsuite(self, tags, testsuite_obj, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_testsuite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        'tags, testcase_obj, expected',
        (
            ('foo', Alpha().test_one, True),
            ({'color': 'red'}, Alpha().test_two, True),
            ({'color': 'blue'}, Alpha().test_two, False),
            (('foo', 'baz'), Beta().test_one, False),
            (
                {'simple': ('foo', 'baz'), 'speed': 'slow'},
                Beta().test_two, True
            ),
            (('foo', 'bar', 'baz'), Gamma().test_four, True),
            (('one', 'two', 'three'), Gamma().test_four, False),
        )
    )
    def test_filter_testcase(self, tags, testcase_obj, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_testcase(testcase_obj)) == expected


class TestTagsAll(object):

    @pytest.mark.parametrize(
        'tags, multitest, expected',
        (
            ('foo', multitest_A, True),
            (('foo', 'something', 'else'), multitest_A, False),
            ('bar', multitest_A, False),
            ({'color': 'blue'}, multitest_A, True),
            (('bar', 'baz'), multitest_F, True),
            (
                {'color': 'yellow', 'simple': 'bar', 'speed': 'slow'},
                multitest_F, True
            ),
            (
                {'color': 'orange', 'simple': 'bat', 'speed': 'medium'},
                multitest_F, False
            )
        )
    )
    def test_filter_instance(self, tags, multitest, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_instance(multitest)) == expected

    @pytest.mark.parametrize(
        'tags, testsuite_obj, expected',
        (
            ('foo', Alpha(), True),
            (('foo', 'something', 'else'), Alpha(), False),
            ('bar', Alpha(), False),
            ({'color': ('blue', 'yellow')}, Alpha(), False),
            ({'color': ('blue', 'yellow')}, Beta(), True),
            ({'color': 'blue'}, Alpha(), True),
            (('bar', 'baz'), Gamma(), False),
            (
                {'color': 'yellow', 'simple': 'bar', 'speed': 'slow'},
                Gamma(), False
            ),
        )
    )
    def test_filter_testsuite(self, tags, testsuite_obj, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_testsuite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        'tags, testcase_obj, expected',
        (
            ('foo', Alpha().test_one, True),
            ({'color': 'red'}, Alpha().test_two, True),
            ({'color': 'blue'}, Alpha().test_two, False),
            (('foo', 'baz'), Beta().test_one, False),
            ({'simple': 'bar', 'speed': 'slow'}, Beta().test_two, True),
            (
                {'simple': ('foo', 'baz'), 'speed': 'slow'},
                Beta().test_two, False
            ),
            (('foo', 'bar', 'baz'), Gamma().test_four, False),
            (('foo', 'baz'), Gamma().test_four, True),
        )
    )
    def test_filter_testcase(self, tags, testcase_obj, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_testcase(testcase_obj)) == expected


class TestPattern(object):

    @pytest.mark.parametrize(
        'pattern, multitest, expected',
        (
            ('AAA', multitest_A, True),
            ('AA', multitest_A, False),
            ('AAAA', multitest_A, False),
            ('A*', multitest_A, True),
            ('A*:*', multitest_A, True),
            ('A*:*:*', multitest_A, True),
            ('AAA:foo:bar', multitest_A, True),
        )
    )
    def test_filter_instance(self, pattern, multitest, expected):
        filter_obj = filtering.Pattern(pattern)
        assert bool(filter_obj.filter_instance(multitest)) == expected

    @pytest.mark.parametrize(
        'pattern, testsuite_obj, expected',
        (
            ('*', Alpha(), True),
            ('*:*', Alpha(), True),
            ('*:*:*', Alpha(), True),
            ('AAA:Alpha', Alpha(), True),
            ('XXX:Alpha', Alpha(), True),
            ('*:Alpha', Alpha(), True),
            ('*:Al*', Alpha(), True),
            ('*:Alpha:foo', Alpha(), True),
            ('*:Al*:foo', Alpha(), True),
            ('*:B*:*', Alpha(), False),
            # suite_name func overrides class name
            ('*:Beta:*', Beta(), False),
            ('*:Beta - Custom:*', Beta(), True),
        )
    )
    def test_filter_testsuite(self, pattern, testsuite_obj, expected):
        filter_obj = filtering.Pattern(pattern=pattern)
        assert bool(filter_obj.filter_testsuite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        'pattern, testcase_obj, expected',
        (
            ('*', Alpha().test_one, True),
            ('*:*', Alpha().test_one, True),
            ('*:*:*', Alpha().test_one, True),
            ('*:*:test_o*', Alpha().test_one, True),
            ('*:*:test_one', Alpha().test_one, True),
            ('XXX:YYY:test_one', Alpha().test_one, True),
            ('*:*:test_two', Alpha().test_one, False),
        )
    )
    def test_filter_testcase(self, pattern, testcase_obj, expected):
        filter_obj = filtering.Pattern(pattern=pattern)
        assert bool(filter_obj.filter_testcase(testcase_obj)) == expected

    def test_filter_initialization_error(self):
        """
            Pattern filter should raise error if
            pattern depth exceeds MAX_LEVEL
        """
        with pytest.raises(ValueError):
            filtering.Pattern('foo:bar:baz:bat')


class DummyFilter(filtering.Filter):
    """Mock filter to be used with meta filter comparisons"""

    def __repr__(self):
        return str(self.__class__)

    def __eq__(self, other):
        return self.__class__ is other.__class__


class AlphaFilter(DummyFilter):
    pass


class BetaFilter(DummyFilter):
    pass


class GammaFilter(DummyFilter):
    pass


class TestFilterCompositions(object):

    def test_or(self):
        filter_1 = AlphaFilter() | BetaFilter()
        filter_2 = filtering.Or(AlphaFilter(), BetaFilter())
        assert filter_1 == filter_2

    def test_or_associativity(self):
        filter_1 = AlphaFilter() | (BetaFilter() | GammaFilter())
        filter_2 = (AlphaFilter() | BetaFilter()) | GammaFilter()
        filter_3 = AlphaFilter() | BetaFilter() | GammaFilter()
        assert filter_1 == filter_2 == filter_3

    def test_and(self):
        filter_1 = AlphaFilter() & BetaFilter()
        filter_2 = filtering.And(AlphaFilter(), BetaFilter())
        assert filter_1 == filter_2

    def test_and_associativity(self):
        filter_1 = AlphaFilter() & (BetaFilter() & GammaFilter())
        filter_2 = (AlphaFilter() & BetaFilter()) & GammaFilter()
        filter_3 = AlphaFilter() & BetaFilter() & GammaFilter()
        assert filter_1 == filter_2 == filter_3

    def test_not(self):
        assert ~AlphaFilter() == filtering.Not(AlphaFilter())
        assert AlphaFilter() == ~~AlphaFilter()
