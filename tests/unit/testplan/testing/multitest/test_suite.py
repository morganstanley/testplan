"""Unit tests for the testplan.testing.multitest.suite module."""

import functools
import re
from unittest import mock

import pytest

from testplan.common.utils.exceptions import should_raise
from testplan.common.utils.interface import MethodSignatureMismatch
from testplan.common.utils.strings import format_description
from testplan.testing.multitest import suite
from testplan.testing.multitest import test_metadata
from testplan.testing import tagging


@suite.testsuite
class MySuite1:
    def pre_testcase(self, name, env, result):
        pass

    def post_testcase(self, name, env, result):
        pass

    @suite.testcase
    def case1(self, env, result):
        pass

    @suite.skip_if(lambda testsuite: True)
    @suite.testcase
    def case2(self, env, result):
        pass

    @suite.testcase
    def case3(self, env, result):
        pass


@suite.testsuite(tags="A")
class MySuite2:
    @suite.testcase(tags="B")
    def case1(self, env, result):
        pass

    @suite.skip_if(lambda testsuite: True)
    @suite.testcase(tags={"c": "C"})
    def case2(self, env, result):
        pass

    @suite.testcase(tags={"d": ["D1", "D2"]})
    def case3(self, env, result):
        pass


@suite.testsuite
class MySuite3:
    @suite.testcase(parameters=(1, 2, 3))
    def case(self, env, result, param):
        pass


@suite.testsuite
class MySuite4:
    @suite.testcase(execution_group="group_0")
    def case1(self, env, result):
        pass

    @suite.testcase(execution_group="group_1")
    def case2(self, env, result):
        pass

    @suite.testcase(execution_group="group_0")
    def case3(self, env, result):
        pass

    @suite.testcase(execution_group="group_1")
    def case4(self, env, result):
        pass

    @suite.testcase(parameters=(1, 2, 3), execution_group="group_parallel")
    def case(self, env, result, param):
        pass


def skip_func(testsuite):  # pylint: disable=unused-argument
    return True


@suite.skip_if_testcase(skip_func)
@suite.testsuite(name="Skipped Suite")
class MySuite5:
    @suite.testcase
    def case1(self, env, result):
        result.equal(1, 2)

    @suite.skip_if(skip_func, lambda testsuite: False)
    @suite.testcase
    def case2(self, env, result):
        result.equal(1, 1)


def test_basic_suites():
    mysuite = MySuite1()

    cases = ("case1", "case2", "case3")
    assert tuple(mysuite.__testcases__) == cases
    assert "pre_testcase" not in mysuite.__testcases__
    assert "post_testcase" not in mysuite.__testcases__

    for method in suite.get_testcase_methods(MySuite1):
        assert method.__name__ in cases
        assert callable(method)

    for method in mysuite.get_testcases():
        assert method.__name__ in cases
        assert callable(method)


def test_basic_suite_tags():
    mysuite = MySuite2()

    assert mysuite.__tags__ == {"simple": {"A"}}

    case_dict = {
        "case1": {"simple": {"B"}},
        "case2": {"c": {"C"}},
        "case3": {"d": {"D2", "D1"}},
    }

    for method in mysuite.get_testcases():
        assert method.__tags__ == case_dict[method.__name__]
        assert method.__tags_index__ == tagging.merge_tag_dicts(
            case_dict[method.__name__], mysuite.__tags__
        )


def test_basic_parametrization():
    mysuite = MySuite3()
    cases = ("case__param_1", "case__param_2", "case__param_3")
    assert tuple(mysuite.__testcases__) == cases

    for method in mysuite.get_testcases():
        assert method.__name__ in cases
        assert callable(method)


def test_basic_execution_group():
    mysuite = MySuite4()

    for i, method in enumerate(mysuite.get_testcases()):
        if method.__name__.startswith("case__"):
            assert method.execution_group == "group_parallel"
        else:
            assert method.execution_group == "group_{}".format(i % 2)


def test_skip_if_predicates():
    mysuite = MySuite1()
    assert len(getattr(mysuite, "case2").__skip__) == 1
    assert getattr(mysuite, "case2").__skip__[0](mysuite)

    mysuite = MySuite5()
    assert len(getattr(mysuite, "case1").__skip__) == 1
    assert len(getattr(mysuite, "case2").__skip__) == 3
    # ``skip_func`` is added to ``MySuite5.__skip__`` twice
    assert (
        getattr(mysuite, "case2").__skip__[0]
        == getattr(mysuite, "case2").__skip__[2]
    )
    assert getattr(mysuite, "case1").__skip__[0](mysuite)
    assert getattr(mysuite, "case2").__skip__[0](mysuite)
    assert not getattr(mysuite, "case2").__skip__[1](mysuite)


def incorrect_case_signature1():
    @suite.testsuite
    class _:
        @suite.testcase
        def case1(self, envs, result):
            pass


def incorrect_case_signature2():
    @suite.testsuite
    class _:
        @suite.testcase
        def case1(self, env, results):
            pass


def test_testcase_signature():
    pattern = re.compile(
        (
            r".*Expected arguments for case1 are \['self', 'env', 'result'\] "
            r"or their underscore-prefixed variants, "
            r"not \['self', 'envs', 'result'\].*"
        )
    )
    should_raise(
        MethodSignatureMismatch, incorrect_case_signature1, pattern=pattern
    )
    pattern = re.compile(
        (
            r".*Expected arguments for case1 are \['self', 'env', 'result'\] "
            r"or their underscore-prefixed variants, "
            r"not \['self', 'env', 'results'\].*"
        )
    )
    should_raise(
        MethodSignatureMismatch, incorrect_case_signature2, pattern=pattern
    )


def incorrent_skip_if_signature1():
    @suite.testsuite
    class _:
        @suite.skip_if(lambda what: True)
        @suite.testcase
        def case1(self, env, result):
            pass


def test_skip_if_signature():
    pattern = re.compile(
        r".*Expected arguments for <lambda> are \['testsuite'\] or their "
        r"underscore-prefixed variants, not \['what'\].*"
    )
    try:
        should_raise(
            MethodSignatureMismatch,
            incorrent_skip_if_signature1,
            pattern=pattern,
        )
    finally:
        # Reset the global __TESTCASES__ list so that it doesn't contain a
        # "case1" entry.
        suite.__TESTCASES__ = []


@pytest.mark.parametrize(
    "text,expected",
    (
        ("", ""),
        ("foo", "foo"),
        ("  foo", "foo"),
        ("foo", "foo"),
        ("  foo  \n    bar\n\n", "  foo\n  bar"),
        ("\t\tfoo  \n   bar\n\n", "  foo\n bar"),
        ("  foo\n    bar\n\n", "  foo\nbar"),
    ),
)
def test_format_description(text, expected):
    format_description(text) == expected


def test_location_metadata_not_resolved_at_decoration_time():
    """Decorating a suite/testcase must not call ``LocationMetadata.from_object``."""
    with mock.patch.object(
        test_metadata.LocationMetadata,
        "from_object",
        wraps=test_metadata.LocationMetadata.from_object,
    ) as spy:

        @suite.testsuite
        class LazyMetadataSuite:
            @suite.testcase
            def case_one(self, env, result):
                pass

            @suite.testcase(parameters=tuple(range(5)))
            def case_param(self, env, result, value):
                pass

        assert spy.call_count == 0


def test_parametrized_testcases_share_one_location_resolution():
    """All variants of a parametrized template resolve metadata once."""

    @suite.testsuite
    class CachedParamSuite:
        @suite.testcase(parameters=tuple(range(20)))
        def case(self, env, result, value):
            pass

    instance = CachedParamSuite()
    testcases = instance.get_testcases()
    assert len(testcases) == 20

    with mock.patch.object(
        test_metadata.LocationMetadata,
        "from_object",
        wraps=test_metadata.LocationMetadata.from_object,
    ) as spy:
        for tc in testcases:
            suite.get_testcase_metadata(tc)

        assert spy.call_count == 1


def test_skipped_case_reports_original_location():
    """``_gen_skipped_case`` must preserve the original testcase's location."""

    @suite.testsuite
    class OriginalSuite:
        @suite.testcase
        def case_x(self, env, result):
            pass

    # ``_gen_skipped_case`` runs against the bound method
    # taken from a suite instance.
    instance = OriginalSuite()
    orig_case = getattr(instance, "case_x")
    original_metadata = suite.get_testcase_metadata(orig_case)

    skipped = suite._gen_skipped_case("manual skip", orig_case)
    skipped_metadata = suite.get_testcase_metadata(skipped)

    assert skipped_metadata.location == original_metadata.location


def test_location_metadata_unwraps_functools_wraps():
    """``from_object`` resolves to the original through ``functools.wraps``."""

    def deco(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        return inner

    def original():
        pass

    wrapped = deco(original)

    loc_original = test_metadata.LocationMetadata.from_object(original)
    loc_wrapped = test_metadata.LocationMetadata.from_object(wrapped)

    assert loc_original is not None
    assert loc_wrapped is not None
    assert loc_wrapped.file == loc_original.file
    assert loc_wrapped.line_no == loc_original.line_no
