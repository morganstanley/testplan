"""Unit tests for MultiTest base functionality."""

import os

from testplan.common.utils import path
from testplan.testing import multitest
from testplan.testing.multitest import base
from testplan.testing import filtering
from testplan.testing import ordering
from testplan import defaults
from testplan import report
from testplan.common import entity

# TODO: shouldn't need to specify these...
MTEST_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


def test_multitest_runpath():
    """Test setting of runpath."""
    # # No runpath specified
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], **MTEST_DEFAULT_PARAMS
    )
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == path.default_runpath(mtest)
    assert mtest._runpath == path.default_runpath(mtest)

    # runpath in local cfg
    custom = os.path.join("", "var", "tmp", "custom")
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], runpath=custom, **MTEST_DEFAULT_PARAMS
    )
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == custom
    assert mtest._runpath == custom

    # runpath in global cfg
    global_runpath = os.path.join("", "var", "tmp", "global_level")
    par = base.MultiTestConfig(name="Mtest", suites=[], runpath=global_runpath)
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], **MTEST_DEFAULT_PARAMS
    )
    mtest.cfg.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == global_runpath
    assert mtest._runpath == global_runpath

    # runpath in global cfg and local
    global_runpath = os.path.join("", "var", "tmp", "global_level")
    local_runpath = os.path.join("", "var", "tmp", "local_runpath")
    par = base.MultiTestConfig(name="Mtest", suites=[], runpath=global_runpath)
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], runpath=local_runpath, **MTEST_DEFAULT_PARAMS
    )
    mtest.cfg.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == local_runpath
    assert mtest._runpath == local_runpath


@multitest.testsuite
class Suite(object):
    """Basic testsuite."""

    @multitest.testcase
    def case(self, env, result):
        """Basic testcase."""
        result.true(True)

    @multitest.testcase(parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase."""
        result.gt(val, 0)


@multitest.testsuite
class ParallelSuite(object):
    """Suite with parallelisable testcases."""

    @multitest.testcase(execution_group="A")
    def case1(self, env, result):
        """Testcase 1"""
        result.eq(0, 0)

    @multitest.testcase(execution_group="A")
    def case2(self, env, result):
        """Testcase 2"""
        result.eq(1, 1)

    @multitest.testcase(execution_group="A")
    def case3(self, env, result):
        """Testcase 3"""
        result.eq(2, 2)

    @multitest.testcase(execution_group="B", parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase"""
        result.gt(val, 0)


EXPECTED_REPORT_SKELETON = report.TestGroupReport(
    name="MTest",
    category=report.ReportCategories.MULTITEST,
    uid="MTest",
    env_status=entity.ResourceStatus.STOPPED,
    entries=[
        report.TestGroupReport(
            name="Suite",
            description="Basic testsuite.",
            category=report.ReportCategories.TESTSUITE,
            uid="Suite",
            parent_uids=["MTest"],
            entries=[
                report.TestCaseReport(
                    name="case",
                    description="Basic testcase.",
                    uid="case",
                    parent_uids=["MTest", "Suite"],
                ),
                report.TestGroupReport(
                    name="parametrized",
                    description="Parametrized testcase.",
                    category=report.ReportCategories.PARAMETRIZATION,
                    uid="parametrized",
                    parent_uids=["MTest", "Suite"],
                    entries=[
                        report.TestCaseReport(
                            name="parametrized__val_1",
                            uid="parametrized__val_1",
                            parent_uids=["MTest", "Suite", "parametrized"],
                        ),
                        report.TestCaseReport(
                            name="parametrized__val_2",
                            uid="parametrized__val_2",
                            parent_uids=["MTest", "Suite", "parametrized"],
                        ),
                        report.TestCaseReport(
                            name="parametrized__val_3",
                            uid="parametrized__val_3",
                            parent_uids=["MTest", "Suite", "parametrized"],
                        ),
                    ],
                ),
            ],
        )
    ],
)


def test_dry_run():
    """Test the "dry_run" method which generates an empty report skeleton."""
    mtest = multitest.MultiTest(
        name="MTest", suites=[Suite()], **MTEST_DEFAULT_PARAMS
    )
    result = mtest.dry_run()
    report_skeleton = result.report

    # Comparing the serialized reports makes it much easier to spot any
    # inconsistencies.
    assert report_skeleton.serialize() == EXPECTED_REPORT_SKELETON.serialize()


def test_run_all_tests():
    """Test running all tests."""
    mtest = multitest.MultiTest(
        name="MTest", suites=[Suite()], **MTEST_DEFAULT_PARAMS
    )
    mtest_report = mtest.run_tests()
    assert mtest_report.passed
    assert mtest_report.name == "MTest"
    assert mtest_report.category == report.ReportCategories.MULTITEST
    assert len(mtest_report.entries) == 1  # One suite.

    suite_report = mtest_report.entries[0]
    assert suite_report.passed
    assert suite_report.name == "Suite"
    assert suite_report.category == report.ReportCategories.TESTSUITE
    assert len(suite_report.entries) == 2  # Two testcases.

    testcase_report = suite_report.entries[0]
    assert testcase_report.passed
    assert testcase_report.name == "case"
    assert testcase_report.category == report.ReportCategories.TESTCASE
    assert len(testcase_report.entries) == 1  # One assertion.

    truth_assertion = testcase_report.entries[0]
    assert truth_assertion["passed"]
    assert truth_assertion["type"] == "IsTrue"
    assert truth_assertion["expr"] is True

    param_report = suite_report.entries[1]
    assert param_report.passed
    assert param_report.name == "parametrized"
    assert param_report.category == report.ReportCategories.PARAMETRIZATION
    assert len(param_report.entries) == 3  # Three parametrized testcases

    for i, testcase_report in enumerate(param_report.entries):
        assert testcase_report.passed
        assert testcase_report.name == "parametrized__val_{}".format(i + 1)
        assert testcase_report.category == report.ReportCategories.TESTCASE
        assert len(testcase_report.entries) == 1  # One assertion

        greater_assertion = testcase_report.entries[0]
        assert greater_assertion["passed"]
        assert greater_assertion["type"] == "Greater"
        assert greater_assertion["first"] == i + 1
        assert greater_assertion["second"] == 0


def test_run_tests_parallel():
    """Test running tests in parallel via an execution group."""
    # Since we have at most three testcases in any one execution group,
    # use three threads in the thread pool to save on resources.
    mtest = multitest.MultiTest(
        name="MTest",
        suites=[ParallelSuite()],
        thread_pool_size=3,
        **MTEST_DEFAULT_PARAMS
    )
    mtest_report = mtest.run_tests()
    assert mtest_report.passed
    assert mtest_report.name == "MTest"
    assert mtest_report.category == report.ReportCategories.MULTITEST
    assert len(mtest_report.entries) == 1  # One suite.

    suite_report = mtest_report.entries[0]
    assert suite_report.passed
    assert suite_report.name == "ParallelSuite"
    assert suite_report.category == report.ReportCategories.TESTSUITE
    assert len(suite_report.entries) == 4  # Four testcases.

    for i in range(3):
        case_name = "case{}".format(i + 1)
        _check_parallel_testcase(suite_report[case_name], i)

    _check_parallel_param(suite_report["parametrized"])


def _check_parallel_testcase(testcase_report, i):
    """
    Check that ith testcase report in the ParallelSuite is as expected after
    a full run.
    """
    assert testcase_report.name == "case{}".format(i + 1)
    assert testcase_report.category == report.ReportCategories.TESTCASE
    assert len(testcase_report.entries) == 1  # One assertion

    equals_assertion = testcase_report.entries[0]
    assert equals_assertion["passed"]
    assert equals_assertion["type"] == "Equal"
    assert equals_assertion["first"] == i
    assert equals_assertion["second"] == i


def _check_parallel_param(param_report):
    """
    Check the parametrized testcase group from the ParallelSuite is as
    expected after a full run.
    """
    assert param_report.name == "parametrized"
    assert param_report.category == report.ReportCategories.PARAMETRIZATION
    assert len(param_report.entries) == 3  # Three parametrized testcases.

    for i, testcase_report in enumerate(param_report.entries):
        assert testcase_report.name == "parametrized__val_{}".format(i + 1)
        assert testcase_report.category == report.ReportCategories.TESTCASE
        assert len(testcase_report.entries) == 1  # One assertion

        greater_assertion = testcase_report.entries[0]
        assert greater_assertion["passed"]
        assert greater_assertion["type"] == "Greater"
        assert greater_assertion["first"] == i + 1
        assert greater_assertion["second"] == 0
