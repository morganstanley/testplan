"""Unit tests for the testplan.testing.multitest.suite module."""

import re

import pytest

from testplan.common.utils.exceptions import should_raise
from testplan.common.utils.interface import MethodSignatureMismatch
from testplan.common.utils.strings import format_description
from testplan.testing.multitest import suite
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
