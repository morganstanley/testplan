"""TODO."""

from unittest import mock

import pytest
from schema import SchemaError

from testplan.defaults import MAX_TEST_NAME_LENGTH
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testcase, testsuite, skip_if
from testplan.common.utils.callable import pre, post

from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    Status,
)


@testsuite(name="Test Suite")
class Suite1(object):
    def setup(self, env, result):
        result.equal(2, 2)

    def teardown(self, env):
        pass

    def pre_testcase(self, name, env, result):
        result.equal(2, 2)
        result.contain("case", name)

    def post_testcase(self, name, env, result):
        result.equal(2, 2)
        result.contain("case", name)

    @testcase
    def case1(self, env, result):
        result.equal(1, 2)

    @testcase
    def case2(self, env, result):
        result.equal(1, 1)

    @skip_if(lambda testsuite: True)
    @testcase
    def case3(self, env, result):
        result.equal(1, 1)


@testsuite(name=lambda cls_name, suite: "{}__{}".format(cls_name, suite.val))
class Suite2(object):
    def __init__(self, val):
        self.val = val

    def setup(self, env):
        pass

    def teardown(self, env, result):
        result.equal(1, 2)

    def pre_testcase(self, name, env, result, kwargs):
        if kwargs.get("a"):
            result.log("Param a: {}".format(kwargs["a"]))
        if kwargs.get("b"):
            result.log("Param b: {}".format(kwargs["b"]))
        result.equal(2, 2)
        result.contain("case", name)

    def post_testcase(self, name, env, result):
        result.equal(2, 2)
        result.contain("case", name)
        if name == "case5":
            raise RuntimeError("raise for no reason")

    @testcase(parameters=(("aa", "bb"), ("aaa", "bbb")))
    def case4(self, env, result, a, b):
        result.equal(2, 2)

    @testcase
    def case5(self, env, result):
        result.equal(1, 2)

    @skip_if(lambda testsuite: True)
    @testcase
    def case6(self, env, result):
        result.equal(1, 1)


def test_basic_multitest(mockplan):
    """Basic test for suite decorator."""
    mtest = MultiTest(name="MTest", suites=[Suite1(), Suite2(0), Suite2(1)])
    mockplan.add(mtest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = mockplan.run()

    assert res.run is True
    assert isinstance(res.test_results["MTest"].report, TestGroupReport)
    assert len(res.test_results["MTest"].report.entries) == 3
    assert isinstance(mockplan.report, TestReport)
    assert len(mockplan.report.entries) == 1  # 1 Multitest

    mt_entry = mockplan.report.entries[0]
    assert isinstance(mt_entry, TestGroupReport)
    assert len(mt_entry.entries) == 3  # 2 Suites
    assert mt_entry.entries[0].name == "Test Suite"
    assert mt_entry.entries[0].uid == "Test Suite"
    assert mt_entry.entries[1].name == "Suite2__0"
    assert mt_entry.entries[1].uid == "Suite2__0"
    assert mt_entry.entries[2].name == "Suite2__1"
    assert mt_entry.entries[2].uid == "Suite2__1"

    for st_entry in mt_entry.entries:
        assert isinstance(st_entry, TestGroupReport)
        assert len(st_entry.entries) == 4  # 4 entries in each suites

        for tc_entry in st_entry.entries:
            if tc_entry.name == "case4":
                assert isinstance(tc_entry, TestGroupReport)
                assert tc_entry.category == ReportCategories.PARAMETRIZATION
                assert len(tc_entry.entries) == 2  # 2 generated testcases
            else:
                assert isinstance(tc_entry, TestCaseReport)
                if tc_entry.name == "case5":
                    assert tc_entry.status == Status.ERROR
                    assert "raise for no reason" in tc_entry.logs[0]["message"]


@pytest.mark.parametrize(
    "suite_name", ("s" * (MAX_TEST_NAME_LENGTH + 1), "My::Suite")
)
def test_unwanted_testsuite_name(mockplan, suite_name):
    """
    Warning for inappropriate custom suite name.
    1. Suite name too long
    2. Colon in suite name
    """
    with mock.patch("warnings.warn", return_value=None) as mock_warn:

        @testsuite(name=suite_name)
        class MySuite(object):
            @testcase
            def sample_test(self, env, result):
                pass

        multitest = MultiTest(name="MTest", suites=[MySuite()])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

    mock_warn.assert_called_once()


def test_duplicate_testsuite_names(mockplan):
    """Raises when duplicate suite names found."""
    with pytest.raises(SchemaError):

        @testsuite
        class MySuite(object):
            def __init__(self, val):
                self.val = val

            @testcase
            def sample_test(self, env, result):
                pass

        multitest = MultiTest(name="MTest", suites=[MySuite(0), MySuite(1)])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

        pytest.fail("Duplicate test suite name found in a Multitest.")


@pytest.mark.parametrize(
    "deco, attr_name", ((testsuite, 123), (testsuite(name=123), "My Suite"))
)
def test_invalid_name_attribute_in_suite_class(mockplan, deco, attr_name):
    """
    User should not define invalid attribute `name` in a test suite object.
    Note: This only happens when @testsuite is used but not @testsuite()
    """
    with pytest.raises(TypeError):

        class MySuite(object):
            name = attr_name

            @testcase
            def sample_test(self, env, result):
                pass

        MySuite = deco(MySuite)
        multitest = MultiTest(name="MyMultitest", suites=[MySuite()])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

        pytest.fail("Attribute `name` defined in test suite class is invalid.")


def test_unexpected_name_attribute_in_suite_object(mockplan):
    """
    User cannot define attribute `name` in a test suite object because
    it is reserved by Testplan.
    """
    with pytest.raises(SchemaError):  # `AttributeError` caught by Schema

        @testsuite
        class MySuite(object):
            @testcase
            def sample_test(self, env, result):
                pass

        suite = MySuite()
        suite.name = lambda cls_name, suite: cls_name
        multitest = MultiTest(name="MyMultitest", suites=[suite])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

        pytest.fail("Attribute `name` of test suite object is invalid.")


def test_testcase_related_with_inivalid_arguments_in_suite_object(mockplan):
    """
    ``pre_testcase`` and ``post_testcase`` methods should have argument
    like [self, name, env, result] or [self, name, env, result, kwargs].
    """

    @testsuite
    class MySuite(object):
        def pre_testcase(self, name, env, result, kwargs):  # valid
            result.dict.log(kwargs)

        def post_testcase(self, name, env, result, my_arg):  # invalid
            pass

        @testcase
        def sample_test(self, env, result):
            pass

        @testcase(parameters=(("foo", "bar"),))
        def param_test(self, env, result, x, y):
            pass

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[MySuite()], stop_on_error=False)
    )
    with log_propagation_disabled(TESTPLAN_LOGGER):
        mockplan.run()

    multitest_report = mockplan.result.report["MyMultitest"]
    case_report = multitest_report["MySuite"]["sample_test"]
    param_case_report = multitest_report["MySuite"]["param_test"].entries[0]

    assert multitest_report.status == Status.ERROR
    assert "MethodSignatureMismatch" in case_report.logs[0]["message"]
    assert len(case_report.entries[0]["flattened_dict"]) == 0
    assert "MethodSignatureMismatch" in param_case_report.logs[0]["message"]
    assert len(param_case_report.entries[0]["flattened_dict"]) == 2


def test_pre_post_on_testcase(mockplan):
    def pre_fn(self, env, result):
        result.log("pre_fn")

    def post_fn(self, env, result):
        result.log("post_fn")

    @testsuite
    class SimpleTest(object):
        def setup(self, env, result):
            result.log("setup")

        def teardown(self, env, result):
            result.log("tear down")

        def pre_testcase(self, name, env, result, kwargs):
            result.log(f"name = {name}", description="pre_testcase")
            if kwargs:
                result.dict.log(kwargs, description="kwargs")

        def post_testcase(self, name, env, result, kwargs):
            result.log(f"name = {name}", description="post_testcase")
            if kwargs:
                result.dict.log(kwargs, description="kwargs")

        @pre(pre_fn)
        @post(post_fn)
        @testcase
        def add_simple(self, env, result):
            result.equal(10 + 5, 15)

        @testcase(
            parameters=((3, 3, 6), (7, 8, 15)),
            custom_wrappers=[pre(pre_fn), post(post_fn)],
        )
        def add_param(self, env, result, a, b, expect):
            result.equal(a + b, expect)

    mockplan.add(MultiTest(name="MyMultitest", suites=[SimpleTest()]))
    with log_propagation_disabled(TESTPLAN_LOGGER):
        mockplan.run()

    multitest_report = mockplan.result.report["MyMultitest"]
    case_report = multitest_report["SimpleTest"]["add_simple"]
    param_case_report = multitest_report["SimpleTest"]["add_param"].entries[0]

    assert multitest_report.status == Status.PASSED
    assert case_report.entries[0]["message"] == "name = add_simple"
    assert case_report.entries[1]["message"] == "pre_fn"

    assert (
        param_case_report.entries[0]["message"]
        == "name = add_param <a=3, b=3, expect=6>"
    )
    assert param_case_report.entries[2]["message"] == "pre_fn"
