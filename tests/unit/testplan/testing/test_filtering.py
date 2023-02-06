import pickle

import pytest

from testplan.testing import filtering
from testplan.testing.multitest import MultiTest, testcase, testsuite


@testsuite(tags="foo")
class Alpha:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_three(self, env, result):
        pass


@testsuite(
    tags="bar",
    name=lambda cls_name, suite: cls_name + " -- Custom",
)
class Beta:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"color": "blue", "speed (-)_tag": "slow"})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": "yellow (-)_tag", "speed (-)_tag": "fast"})
    def test_three(self, env, result):
        pass


@testsuite(tags=("foo", "baz"))
class Gamma:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"speed (-)_tag": "fast"})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": "green"})
    def test_three(self, env, result):
        pass

    @testcase(tags={"color": ("blue", "red")})
    def test_four(self, env, result):
        pass


@testsuite
class Delta:
    @testcase(parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        pass


multitest_A = MultiTest(name="AAA", suites=[Alpha()])
multitest_B = MultiTest(name="BBB", suites=[Beta()])
multitest_C = MultiTest(name="CCC", suites=[Gamma()])
multitest_D = MultiTest(name="DDD", suites=[Alpha(), Beta()])
multitest_E = MultiTest(name="EEE", suites=[Beta(), Gamma()])
multitest_F = MultiTest(name="FFF", suites=[Alpha(), Beta(), Gamma()])


class TestTags:
    @pytest.mark.parametrize(
        "tags, multitest, expected",
        (
            ("foo", multitest_A, True),
            (("foo", "something", "else"), multitest_A, True),
            ("bar", multitest_A, False),
            ({"color": "blue"}, multitest_A, True),
            (("bar", "baz"), multitest_F, True),
            (
                {
                    "color": "yellow (-)_tag",
                    "simple": "bar",
                    "speed (-)_tag": "slow",
                },
                multitest_F,
                True,
            ),
            (
                {"color": "orange", "simple": "bat", "speed (-)_tag": "medium"},
                multitest_F,
                False,
            ),
        ),
    )
    def test_filter_test(self, tags, multitest, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_test(multitest)) == expected

    @pytest.mark.parametrize(
        "tags, testsuite_obj, expected",
        (
            ("foo", Alpha(), True),
            (("foo", "something", "else"), Alpha(), True),
            ("bar", Alpha(), False),
            ({"color": ("blue", "yellow (-)_tag")}, Alpha(), True),
            ({"color": ("blue", "yellow (-)_tag")}, Beta(), True),
            ({"color": "blue"}, Alpha(), True),
            (("bar", "baz"), Gamma(), True),
            (
                {
                    "color": "yellow (-)_tag",
                    "simple": "bar",
                    "speed (-)_tag": "slow",
                },
                Gamma(),
                False,
            ),
        ),
    )
    def test_filter_suite(self, tags, testsuite_obj, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_suite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        "tags, testcase_obj, expected",
        (
            ("foo", Alpha().test_one, True),
            ({"color": "red"}, Alpha().test_two, True),
            ({"color": "blue"}, Alpha().test_two, False),
            (("foo", "baz"), Beta().test_one, False),
            (
                {"simple": ("foo", "baz"), "speed (-)_tag": "slow"},
                Beta().test_two,
                True,
            ),
            (("foo", "bar", "baz"), Gamma().test_four, True),
            (("one", "two", "three"), Gamma().test_four, False),
        ),
    )
    def test_filter_case(self, tags, testcase_obj, expected):
        filter_obj = filtering.Tags(tags=tags)
        assert bool(filter_obj.filter_case(testcase_obj)) == expected

    @pytest.mark.parametrize(
        "tags", (("foo", {"color": "red"}, ("foo", "bar", "baz")))
    )
    def test_pickle(self, tags):
        filter_obj = filtering.Tags(tags=tags)
        assert pickle.loads(pickle.dumps(filter_obj)) == filter_obj


class TestTagsAll:
    @pytest.mark.parametrize(
        "tags, multitest, expected",
        (
            ("foo", multitest_A, True),
            (("foo", "something", "else"), multitest_A, False),
            ("bar", multitest_A, False),
            ({"color": "blue"}, multitest_A, True),
            (("bar", "baz"), multitest_F, True),
            (
                {
                    "color": "yellow (-)_tag",
                    "simple": "bar",
                    "speed (-)_tag": "slow",
                },
                multitest_F,
                True,
            ),
            (
                {"color": "orange", "simple": "bat", "speed (-)_tag": "medium"},
                multitest_F,
                False,
            ),
        ),
    )
    def test_filter_test(self, tags, multitest, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_test(multitest)) == expected

    @pytest.mark.parametrize(
        "tags, testsuite_obj, expected",
        (
            ("foo", Alpha(), True),
            (("foo", "something", "else"), Alpha(), False),
            ("bar", Alpha(), False),
            ({"color": ("blue", "yellow (-)_tag")}, Alpha(), False),
            ({"color": ("blue", "yellow (-)_tag")}, Beta(), True),
            ({"color": "blue"}, Alpha(), True),
            (("bar", "baz"), Gamma(), False),
            (
                {
                    "color": "yellow (-)_tag",
                    "simple": "bar",
                    "speed (-)_tag": "slow",
                },
                Gamma(),
                False,
            ),
        ),
    )
    def test_filter_suite(self, tags, testsuite_obj, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_suite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        "tags, testcase_obj, expected",
        (
            ("foo", Alpha().test_one, True),
            ({"color": "red"}, Alpha().test_two, True),
            ({"color": "blue"}, Alpha().test_two, False),
            (("foo", "baz"), Beta().test_one, False),
            ({"simple": "bar", "speed (-)_tag": "slow"}, Beta().test_two, True),
            (
                {"simple": ("foo", "baz"), "speed (-)_tag": "slow"},
                Beta().test_two,
                False,
            ),
            (("foo", "bar", "baz"), Gamma().test_four, False),
            (("foo", "baz"), Gamma().test_four, True),
        ),
    )
    def test_filter_case(self, tags, testcase_obj, expected):
        filter_obj = filtering.TagsAll(tags=tags)
        assert bool(filter_obj.filter_case(testcase_obj)) == expected

    @pytest.mark.parametrize(
        "tags", (("foo", {"color": "red"}, ("foo", "bar", "baz")))
    )
    def test_pickle(self, tags):
        filter_obj = filtering.TagsAll(tags=tags)
        assert pickle.loads(pickle.dumps(filter_obj)) == filter_obj


class TestPattern:
    @pytest.mark.parametrize(
        "pattern, multitest, expected",
        (
            ("AAA", multitest_A, True),
            ("AA", multitest_A, False),
            ("AAAA", multitest_A, False),
            ("A*", multitest_A, True),
            ("A*:*", multitest_A, True),
            ("A*:*:*", multitest_A, True),
            ("AAA:foo:bar", multitest_A, True),
        ),
    )
    def test_filter_test(self, pattern, multitest, expected):
        filter_obj = filtering.Pattern(pattern)
        assert bool(filter_obj.filter_test(multitest)) == expected

    @pytest.mark.parametrize(
        "pattern, testsuite_obj, expected",
        (
            ("*", Alpha(), True),
            ("*:*", Alpha(), True),
            ("*:*:*", Alpha(), True),
            ("AAA:Alpha", Alpha(), True),
            ("XXX:Alpha", Alpha(), True),
            ("*:Alpha", Alpha(), True),
            ("*:Al*", Alpha(), True),
            ("*:Alpha:foo", Alpha(), True),
            ("*:Al*:foo", Alpha(), True),
            ("*:B*:*", Alpha(), False),
            # Argument ``name`` overrides the original class name
            ("*:Beta:*", Beta(), False),
            ("*:Beta -- Custom:*", Beta(), True),
        ),
    )
    def test_filter_suite(self, pattern, testsuite_obj, expected):
        filter_obj = filtering.Pattern(pattern=pattern)
        # Test suite object gets its `name` after added into a Multitest
        MultiTest(name="MTest", suites=testsuite_obj)
        assert bool(filter_obj.filter_suite(testsuite_obj)) == expected

    @pytest.mark.parametrize(
        "pattern, testcase_obj, expected",
        (
            ("*", Alpha().test_one, True),
            ("*:*", Alpha().test_one, True),
            ("*:*:*", Alpha().test_one, True),
            ("*:*:test_o*", Alpha().test_one, True),
            ("*:*:test_one", Alpha().test_one, True),
            ("XXX:YYY:test_one", Alpha().test_one, True),
            ("*:*:test_two", Alpha().test_one, False),
        ),
    )
    def test_filter_case(self, pattern, testcase_obj, expected):
        filter_obj = filtering.Pattern(pattern=pattern)
        assert bool(filter_obj.filter_case(testcase_obj)) == expected

    def test_filter_parametrized_cases(self):
        """
        Test filtering parametrized testcases.

        Parametrized testcases should match filter patterns for either the
        base parametrization template or the generated testcase name.
        """
        suite = Delta()
        testcases = suite.get_testcases()
        assert len(testcases) == 3  # Expect 3 testcases to be generated.

        testcase = testcases[0]
        for pattern in [
            "*:Delta:parametrized",
            "*:Delta:parametrized <val=1>",
        ]:
            filter_obj = filtering.Pattern(pattern=pattern)
            assert filter_obj.filter_case(testcase)

    def test_filter_initialization_error(self):
        """
        Symbol ":" or "::" can be used as delimiter and MAX_LEVEL parts
        can be generated for matching.
        """
        with pytest.raises(ValueError):
            filtering.Pattern("foo:bar:baz:bat")

    @pytest.mark.parametrize(
        "pattern",
        (
            "*",
            "*:*:*",
            "*:*:test_o*",
            "XXX:YYY:test_one",
        ),
    )
    def test_pickle(self, pattern):
        filter_obj = filtering.Pattern(pattern=pattern)
        assert pickle.loads(pickle.dumps(filter_obj)) == filter_obj


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


class TestFilterCompositions:
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

    def test_pickle(self):
        assert pickle.loads(pickle.dumps(~AlphaFilter())) == ~AlphaFilter()
        assert pickle.loads(
            pickle.dumps(AlphaFilter() & (BetaFilter() | GammaFilter()))
        ) == AlphaFilter() & (BetaFilter() | GammaFilter())
