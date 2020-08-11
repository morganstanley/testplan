"""TODO."""

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
@testsuite(name="Test Suite - One")
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
@testsuite(name="Test Suite")
class Suite2(object):
    def setup(self, env):
        pass

    def suite_name(self):
        return "Another"

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

    mtest = MultiTest(name="Name1", suites=[Suite1(), Suite2()])
    mockplan.add(mtest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = mockplan.run()

    assert res.run is True
    assert isinstance(res.test_results["Name1"].report, TestGroupReport)
    assert len(res.test_results["Name1"].report.entries) == 2
    assert isinstance(mockplan.report, TestReport)
    assert len(mockplan.report.entries) == 1  # 1 Multitest

    mt_entry = mockplan.report.entries[0]
    assert isinstance(mt_entry, TestGroupReport)
    assert len(mt_entry.entries) == 2  # 2 Suites
    assert mt_entry.entries[0].name == "Test Suite - One"
    assert mt_entry.entries[0].uid == "Suite1"
    assert mt_entry.entries[1].name == "Test Suite - Another"
    assert mt_entry.entries[1].uid == "Suite2"

    for st_entry in mt_entry.entries:
        assert isinstance(st_entry, TestGroupReport)
        assert len(st_entry.entries) == 4  # 4 Testcases

        for tc_entry in st_entry.entries:
            if tc_entry.name == "case4":
                assert isinstance(tc_entry, TestGroupReport)
                assert tc_entry.category == ReportCategories.PARAMETRIZATION
                assert len(tc_entry.entries) == 2  # 2 generated testcases
            else:
                assert isinstance(tc_entry, TestCaseReport)
