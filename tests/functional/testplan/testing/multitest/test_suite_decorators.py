"""TODO."""

import pytest
import mock
from schema import SchemaError

from testplan.defaults import MAX_TEST_NAME_LENGTH
from testplan.testing.multitest import MultiTest

from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    Status,
)
from testplan.testing.multitest.suite import (
    testcase,
    testsuite,
    skip_if,
    post_testcase,
    pre_testcase,
)


def pre1(name, self, env, result):
    result.contain("case", name)


def post1(name, self, env, result):
    result.contain("case", name)


def pre2(name, self, env, result, a=None, b=None):
    result.contain("case", name)


def post2(name, self, env, result, a=None, b=None):
    result.contain("case", name)
    if name == "case5":
        raise RuntimeError("post2 raises")


def pre3(name, self, env, result):
    result.contain("case", name)
    if name == "case4":
        raise RuntimeError("pre3 raises")


def post3(name, self, env, result):
    result.contain("case", name)
    raise RuntimeError("post3 raises")


@pre_testcase(pre1)
@post_testcase(post1)
@testsuite(name="Test Suite")
class Suite1(object):
    def setup(self, env, result):
        result.equal(2, 2)

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

    def teardown(self, env):
        pass


@pre_testcase(pre2)
@post_testcase(post2)
@testsuite(name=lambda cls_name, suite: "{}__{}".format(cls_name, suite.val))
class Suite2(object):
    def __init__(self, val):
        self.val = val

    def setup(self, env):
        pass

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

    def teardown(self, env, result):
        result.equal(1, 2)


@pre_testcase(pre3)
@post_testcase(post2, post3)
@testsuite(name="Test Suite")
class Suite3(object):
    @testcase
    def case4(self, env, result):
        result.equal(2, 2)

    @testcase
    def case5(self, env, result):
        result.equal(1, 2)

    @testcase
    def case6(self, env, result):
        result.equal(1, 2)

    @testcase
    def case7(self, env, result):
        result.equal(1, 1)
        raise RuntimeError("case7 raises")


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
                    assert "post2 raises" in tc_entry.logs[0]["message"]


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


def test_post_testcase_methods_executed_on_exception(mockplan):
    """
    Pre-testcase methods or testcase itself may raise exception but
    post-testcases methods must be executed if they have been defined.
    The first exception caught will be recorded in logs of test report.
    """
    mtest = MultiTest(name="MTest", suites=[Suite3()], stop_on_error=False)
    mockplan.add(mtest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = mockplan.run()

    assert res.run is True
    st_entry = mockplan.report.entries[0].entries[0]
    assert len(st_entry) == 4  # 4 testcases

    assert len(st_entry.entries[0]) == 3  # pre3 raised, testcase did not run
    assert "pre3 raises" in st_entry.entries[0].logs[0]["message"]
    assert len(st_entry.entries[1]) == 4  # post2 raised, post3 still run
    assert "post2 raises" in st_entry.entries[1].logs[0]["message"]
    assert len(st_entry.entries[2]) == 4  # post2 went well, post3 raised
    assert "post3 raises" in st_entry.entries[2].logs[0]["message"]
    assert len(st_entry.entries[3]) == 4  # case7 raised, then post3 raises
    assert "case7 raises" in st_entry.entries[3].logs[0]["message"]
