"""TODO."""

import pytest
from schema import SchemaError

from testplan.defaults import MAX_TESTSUITE_NAME_LENGTH
from testplan.testing.multitest import MultiTest

from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.report import (
    TestReport,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
)
from testplan.testing.multitest.suite import (
    testcase,
    testsuite,
    skip_if,
    post_testcase,
    pre_testcase,
)


def pre1(name, self, env, result):
    result.equal(2, 2)
    result.contain("testcase", name)


def post1(name, self, env, result):
    result.equal(2, 2)
    result.contain("testcase", name)


def pre2(name, self, env, result, a=None, b=None):
    result.equal(2, 2)
    result.contain("testcase", name)


def post2(name, self, env, result, a=None, b=None):
    result.equal(2, 2)
    result.contain("testcase", name)


@pre_testcase(pre1)
@post_testcase(post1)
@testsuite(custom_name="Test Suite - One")
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
@testsuite(
    custom_name=lambda self, original_name: "Test Suite - Another {}".format(
        self.val
    )
)
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


def test_basic_multitest(mockplan):

    mtest = MultiTest(name="MTest", suites=[Suite1(), Suite2(1), Suite2(2)])
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
    assert mt_entry.entries[0].name == "Test Suite - One"
    assert mt_entry.entries[0].uid == "Test Suite - One"
    assert mt_entry.entries[1].name == "Test Suite - Another 1"
    assert mt_entry.entries[1].uid == "Test Suite - Another 1"
    assert mt_entry.entries[2].name == "Test Suite - Another 2"
    assert mt_entry.entries[2].uid == "Test Suite - Another 2"

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


def test_invalid_long_testsuite_name(mockplan):
    """Custom naming function should return a valid non-empty string."""
    with pytest.raises(SchemaError):

        long_string = "a" * (MAX_TESTSUITE_NAME_LENGTH + 1)

        @testsuite(custom_name=long_string)
        class MySuite(object):
            def sample_test(self, env, result):
                pass

        multitest = MultiTest(name="MTest", suites=[MySuite()])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

        pytest.fail("Should fail if custom_name returns a very long string.")


def test_duplicate_testsuite_names(mockplan):
    """Custom naming function should return a valid non-empty string."""
    with pytest.raises(SchemaError):

        @testsuite
        class MySuite(object):
            def sample_test(self, env, result):
                pass

        multitest = MultiTest(name="MTest", suites=[MySuite(), MySuite()])
        mockplan.add(multitest)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            mockplan.run()

        pytest.fail("Should fail if 2 Multitests have the same name.")
