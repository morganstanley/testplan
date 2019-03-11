"""TODO."""

from testplan.testing.multitest import MultiTest

from testplan import Testplan
from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.report.testing import (TestReport, TestGroupReport,
                                     TestCaseReport)
from testplan.testing.multitest.suite import (testcase, testsuite, skip_if,
                                              post_testcase, pre_testcase)


def pre(name, self, env, result):
    result.equal(2, 2)
    result.contain('case', name)


def post(name, self, env, result):
    result.equal(2, 2)
    result.contain('case', name)


@pre_testcase(pre)
@post_testcase(post)
@testsuite
class Suite1(object):

    def setup(self, env, result):
        result.equal(2, 2)

    @testcase
    def case1(self, env, result):
        result.equal(1, 2)

    @testcase
    def case2(self, env, result):
        result.equal(1, 1)

    @skip_if(lambda suite: True)
    @testcase
    def case3(self, env, result):
        result.equal(1, 1)

    def teardown(self, env):
        pass


@pre_testcase(pre)
@post_testcase(post)
@testsuite
class Suite2(object):

    def setup(self, env):
        pass

    @testcase
    def case4(self, env, result):
        result.equal(2, 2)

    @testcase
    def case5(self, env, result):
        result.equal(1, 2)

    @skip_if(lambda suite: True)
    @testcase
    def case6(self, env, result):
        result.equal(1, 1)

    def teardown(self, env, result):
        result.equal(1, 2)


def test_basic_multitest():
    plan = Testplan(name='Plan', parse_cmdline=False)

    mtest = MultiTest(name='Name1', suites=[Suite1(), Suite2()])
    plan.add(mtest)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        res = plan.run()

    assert res.run is True
    assert isinstance(res.test_results['Name1'].report, TestGroupReport)
    assert len(res.test_results['Name1'].report.entries) == 2
    assert isinstance(plan.report, TestReport)
    assert len(plan.report.entries) == 1  # 1 Multitest
    for mt_entry in plan.report.entries:
        assert isinstance(mt_entry, TestGroupReport)
        assert len(mt_entry.entries) == 2  # 2 Suites
        for st_entry in mt_entry.entries:
            assert isinstance(st_entry, TestGroupReport)
            assert len(st_entry.entries) == 3  # 3 Testcases
            for tc_entry in st_entry.entries:
                assert isinstance(tc_entry, TestCaseReport)  # Assertions
