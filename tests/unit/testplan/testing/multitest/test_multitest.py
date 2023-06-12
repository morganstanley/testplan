"""Unit tests for MultiTest base functionality."""

import os

import pytest

from testplan.common import entity
from testplan.common.utils import path, testing
from testplan.common.utils.thread import Barrier
from testplan.testing import multitest, filtering, ordering
from testplan.testing.multitest import base
from testplan import defaults, report


MTEST_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


@pytest.fixture
def dummy_mtest():
    mtest = multitest.MultiTest(
        name="MTest",
        suites=[Suite()],
        thread_pool_size=3,
        **MTEST_DEFAULT_PARAMS,
    )
    mtest.dry_run()
    return mtest


def test_iterable_suites():
    @multitest.testsuite
    class TestSuite:
        pass

    testsuite = TestSuite()
    output = base.iterable_suites(testsuite)
    expected = [testsuite]
    assert output == expected

    with pytest.raises(ValueError):
        base.iterable_suites([testsuite, testsuite])


def test_extract_parametrized_testcase_targets():
    entry = {
        "name": "foo",
        "entries": [
            {
                "name": "bar",
            },
            {
                "name": "baz",
            },
        ],
    }
    output = base._extract_parametrized_testcase_targets(entry)
    expected = ["bar", "baz"]
    assert output == expected


def test_extract_testsuite_targets():
    entry = {
        "name": "foo",
        "entries": [
            {
                "name": "bar",
                "category": report.ReportCategories.TESTCASE,
            },
            {
                "name": "baz",
                "category": report.ReportCategories.PARAMETRIZATION,
                "entries": [
                    {
                        "name": "foo_bar",
                    },
                    {
                        "name": "foo_baz",
                    },
                ],
            },
        ],
    }
    output = base._extract_testsuite_targets(entry)
    expected = ["bar", "foo_bar", "foo_baz"]
    assert output == expected


def test_extract_test_targets():
    entry = {
        "name": "foo",
        "category": "multitest",
        "entries": [
            {
                "name": "bar",
                "category": "testsuite",
                "entries": [
                    {
                        "name": "baz",
                        "category": "testcase",
                    },
                ],
            },
        ],
    }
    output = base._extract_test_targets(entry)
    expected = {"bar": ["baz"]}
    assert output == expected


def test_multitest_runpath():
    """Test setting of runpath."""

    class Parent:
        def __init__(self, runpath):
            self.runpath = runpath

    global_runpath = os.path.join("", "var", "tmp", "global_level")
    local_runpath = os.path.join("", "var", "tmp", "local_runpath")

    par = Parent(global_runpath)

    # No runpath specified - take default runpath
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], **MTEST_DEFAULT_PARAMS
    )
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == path.default_runpath(mtest)
    assert mtest._runpath == path.default_runpath(mtest)

    # runpath in local cfg - take local cfg
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], runpath=local_runpath, **MTEST_DEFAULT_PARAMS
    )
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == local_runpath
    assert mtest._runpath == local_runpath

    # runpath in global cfg - take parent's runpath and append uid
    mtest = multitest.MultiTest(
        name="Mtest", suites=[], **MTEST_DEFAULT_PARAMS
    )
    mtest.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == os.path.join(global_runpath, "mtest")
    assert mtest._runpath == os.path.join(global_runpath, "mtest")

    # runpath in global cfg and local - take local cfg
    mtest = multitest.MultiTest(name="Mtest", suites=[], runpath=local_runpath)
    mtest.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == local_runpath
    assert mtest._runpath == local_runpath


@multitest.testsuite
class Suite:
    """Basic testsuite."""

    @multitest.testcase
    def case(self, env, result):
        """Basic testcase."""
        result.true(True)
        assert env.runtime_info.testcase.name == "case"
        assert (
            env.runtime_info.testcase.report.description == "Basic testcase."
        )

    @multitest.testcase(parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase."""
        result.gt(val, 0)
        assert (
            env.runtime_info.testcase.name
            == "parametrized <val={}>".format(val)
        )
        assert (
            env.runtime_info.testcase.report.description
            == "Parametrized testcase."
        )


@multitest.testsuite
class ParallelSuite:
    """
    Suite with parallelisable testcases.

    - using Barrier to make sure they overlap
    - using pytest assertion to do checks while the plan is running, we do not need it in the report

    """

    def __init__(self):
        self._barrier = Barrier(3)

    @multitest.testcase(execution_group="A")
    def case1(self, env, result):
        """Testcase 1"""
        self._barrier.wait()
        result.eq(0, 0)
        assert env.runtime_info.testcase.name == "case1"
        assert env.runtime_info.testcase.report.description == "Testcase 1"
        self._barrier.wait()

    @multitest.testcase(execution_group="A")
    def case2(self, env, result):
        """Testcase 2"""
        self._barrier.wait()
        result.eq(1, 1)
        assert env.runtime_info.testcase.name == "case2"
        assert env.runtime_info.testcase.report.description == "Testcase 2"
        self._barrier.wait()

    @multitest.testcase(execution_group="A")
    def case3(self, env, result):
        """Testcase 3"""
        self._barrier.wait()
        result.eq(2, 2)
        assert env.runtime_info.testcase.name == "case3"
        assert env.runtime_info.testcase.report.description == "Testcase 3"
        self._barrier.wait()

    @multitest.testcase(execution_group="B", parameters=[1, 2, 3])
    def parametrized(self, env, result, val):
        """Parametrized testcase"""
        self._barrier.wait()
        result.gt(val, 0)
        assert (
            env.runtime_info.testcase.name
            == "parametrized <val={}>".format(val)
        )
        self._barrier.wait()


EXPECTED_REPORT_SKELETON = report.TestGroupReport(
    name="MTest",
    description="Basic multitest.",
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
                            name="parametrized <val=1>",
                            description="Parametrized testcase.",
                            uid="parametrized__val_1",
                            parent_uids=["MTest", "Suite", "parametrized"],
                        ),
                        report.TestCaseReport(
                            name="parametrized <val=2>",
                            description="Parametrized testcase.",
                            uid="parametrized__val_2",
                            parent_uids=["MTest", "Suite", "parametrized"],
                        ),
                        report.TestCaseReport(
                            name="parametrized <val=3>",
                            description="Parametrized testcase.",
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
        name="MTest",
        description="Basic multitest.",
        suites=[Suite()],
        **MTEST_DEFAULT_PARAMS,
    )
    result = mtest.dry_run()
    report_skeleton = result.report

    # Comparing the reports to spot any inconsistencies.
    testing.check_report(
        expected=EXPECTED_REPORT_SKELETON, actual=report_skeleton
    )


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
    _check_testcase_report(testcase_report)

    param_report = suite_report.entries[1]
    assert param_report.passed
    assert param_report.name == "parametrized"
    assert param_report.category == report.ReportCategories.PARAMETRIZATION
    assert len(param_report.entries) == 3  # Three parametrized testcases

    for i, testcase_report in enumerate(param_report.entries):
        _check_param_testcase_report(testcase_report, i)


def test_run_tests_parallel():
    """Test running tests in parallel via an execution group."""
    # Since we have at most three testcases in any one execution group,
    # use three threads in the thread pool to save on resources.
    mtest = multitest.MultiTest(
        name="MTest",
        suites=[ParallelSuite()],
        thread_pool_size=3,
        **MTEST_DEFAULT_PARAMS,
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


def test_run_testcases_iter(dummy_mtest):
    """Test running tests iteratively."""
    results = list(dummy_mtest.run_testcases_iter())
    assert len(results) == 8

    attributes, parent_uids = results[0]
    assert parent_uids == ["MTest", "Suite", "case"]
    assert attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    testcase_report, parent_uids = results[1]
    assert parent_uids == ["MTest", "Suite"]
    assert testcase_report.runtime_status == report.RuntimeStatus.FINISHED
    _check_testcase_report(testcase_report)

    for i, (attributes, parent_uids) in enumerate(results[2::2]):
        assert parent_uids == [
            "MTest",
            "Suite",
            "parametrized",
            "parametrized__val_{}".format(i + 1),
        ]
        assert attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    for i, (testcase_report, parent_uids) in enumerate(results[3::2]):
        assert parent_uids == ["MTest", "Suite", "parametrized"]
        assert testcase_report.runtime_status == report.RuntimeStatus.FINISHED
        _check_param_testcase_report(testcase_report, i)


def test_run_testcases_iter_filtered(dummy_mtest):
    """Test running tests iteratively."""
    """Test running tests iteratively."""
    shallow_report = dummy_mtest.report.shallow_serialize()
    shallow_report["entries"] = [
        {
            "name": "Suite",
            "category": "testsuite",
            "entries": [
                {
                    "name": "parametrized",
                    "category": "parametrization",
                    "entries": [
                        {
                            "name": "parametrized <val=1>",
                            "category": "testcase",
                        }
                    ],
                }
            ],
        }
    ]
    results = list(
        dummy_mtest.run_testcases_iter(shallow_report=shallow_report)
    )
    assert len(results) == 2

    attributes, parent_uids = results[0]
    assert parent_uids == [
        "MTest",
        "Suite",
        "parametrized",
        "parametrized__val_1",
    ]
    assert attributes["runtime_status"] == report.RuntimeStatus.RUNNING

    testcase_report, parent_uids = results[1]
    assert parent_uids == ["MTest", "Suite", "parametrized"]
    assert testcase_report.runtime_status == report.RuntimeStatus.FINISHED
    _check_param_testcase_report(testcase_report, 0)


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
        assert testcase_report.name == "parametrized <val={}>".format(i + 1)
        assert testcase_report.category == report.ReportCategories.TESTCASE
        assert len(testcase_report.entries) == 1  # One assertion

        greater_assertion = testcase_report.entries[0]
        assert greater_assertion["passed"]
        assert greater_assertion["type"] == "Greater"
        assert greater_assertion["first"] == i + 1
        assert greater_assertion["second"] == 0


def _check_testcase_report(testcase_report):
    """
    Check the testcase report generated for the "case" testcase from the
    "Suite" testsuite.
    """
    assert testcase_report.passed
    assert testcase_report.name == "case"
    assert testcase_report.category == report.ReportCategories.TESTCASE
    assert len(testcase_report.entries) == 1  # One assertion.

    truth_assertion = testcase_report.entries[0]
    assert truth_assertion["passed"]
    assert truth_assertion["type"] == "IsTrue"
    assert truth_assertion["expr"] is True


def _check_param_testcase_report(testcase_report, i):
    """
    Check the testcase report generated for the ith parametrization of the
    "parametrized" testcase from the "Suite" testsuite.
    """
    assert testcase_report.passed
    assert testcase_report.name == "parametrized <val={}>".format(i + 1)
    assert testcase_report.category == report.ReportCategories.TESTCASE
    assert len(testcase_report.entries) == 1  # One assertion

    greater_assertion = testcase_report.entries[0]
    assert greater_assertion["passed"]
    assert greater_assertion["type"] == "Greater"
    assert greater_assertion["first"] == i + 1
    assert greater_assertion["second"] == 0
