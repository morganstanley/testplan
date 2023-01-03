"""TODO."""

import os

import pytest

from testplan import Testplan, TestplanMock, TestplanResult
from testplan.common.entity import (
    Resource,
    ResourceStatus,
)
from testplan.common.utils.exceptions import should_raise
from testplan.common.utils.path import default_runpath
from testplan.common.utils.testing import argv_overridden
from testplan.runnable import TestRunnerStatus, TestRunner
from testplan.runners.local import LocalRunner
from testplan.report import TestGroupReport, ReportCategories
from testplan.testing.base import Test, TestResult


class DummyDriver(Resource):
    def starting(self):
        self.status.change(ResourceStatus.STARTED)

    def stopping(self):
        self.status.change(ResourceStatus.STOPPED)

    def aborting(self):
        pass


class DummyTestResult(TestResult):
    """TODO."""

    def __init__(self):
        super(DummyTestResult, self).__init__()
        self.custom = None
        self.report = TestGroupReport(
            name="test", category=ReportCategories.TESTGROUP
        )


class DummyTest(Test):
    RESULT = DummyTestResult

    def __init__(self, name="dummyTest"):
        super(DummyTest, self).__init__(name=name)
        self.resources.add(DummyDriver(), uid=self.name)
        self.resources.add(DummyDriver())

    def run_tests(self):
        self._result.custom = "{}Result[{}]".format(
            self.__class__.__name__, self.name
        )

    def main_batch_steps(self):
        self._add_step(self.run_tests)


class MyPool(LocalRunner):  # Start is async
    def __init__(self, name=None):
        super(MyPool, self).__init__()
        self.name = name

    def uid(self):
        return self.name or super(MyPool, self).uid()

    def _execute(self, uid):
        func = self._input[uid]
        test = func()
        test.parent = self
        test.cfg.parent = self.cfg
        test.run()
        self._results[uid] = test.result
        assert isinstance(self._results[uid], DummyTestResult)

    def aborting(self):
        pass


def test_testplan():
    """TODO."""
    from testplan.base import TestplanParser as MyParser

    plan = TestplanMock(name="MyPlan", parser=MyParser)
    assert plan._cfg.name == "MyPlan"
    assert plan._cfg.runnable == TestRunner
    assert plan.cfg.name == "MyPlan"
    assert plan._runnable.cfg.name == "MyPlan"
    # Argument of manager but not of runnable.
    should_raise(AttributeError, getattr, args=(plan._runnable.cfg, "port"))

    assert isinstance(plan.status, TestRunnerStatus)
    assert isinstance(plan._runnable.status, TestRunnerStatus)

    assert "local_runner" in plan.resources

    assert plan.add(DummyTest(name="alice")) == "alice"
    assert plan.add(DummyTest(name="bob")) == "bob"

    assert "pool" not in plan.resources
    plan.add_resource(MyPool(name="pool"))
    assert "pool" in plan.resources

    def task():
        return DummyTest(name="tom")

    assert isinstance(plan.add(task, resource="pool"), str)
    with pytest.raises(ValueError):
        assert plan.add(task, resource="pool")  # duplicate target uid

    assert len(plan.resources["local_runner"]._input) == 2
    for key in ("alice", "bob"):
        assert key in plan.resources["local_runner"]._input
    assert len(plan.resources["pool"]._input) == 1

    res = plan.run()
    assert res.run is True

    assert (
        plan.resources["local_runner"].get("bob").custom
        == "DummyTestResult[bob]"
    )
    assert (
        plan.resources["local_runner"].get("alice").custom
        == "DummyTestResult[alice]"
    )
    for key in plan.resources["pool"]._input.keys():
        assert plan.resources["pool"].get(key).custom == "DummyTestResult[tom]"

    results = plan.result.test_results.values()
    expected = [
        "DummyTestResult[alice]",
        "DummyTestResult[tom]",
        "DummyTestResult[bob]",
    ]
    for res in results:
        should_raise(AttributeError, getattr, args=(res, "decorated_value"))
        assert res.run is True
        assert res.custom in expected
        expected.remove(res.custom)
    assert len(expected) == 0


def test_testplan_decorator():
    """TODO."""
    from testplan import test_plan

    @test_plan(name="MyPlan", port=800, parse_cmdline=False)
    def main1(plan):
        plan.add(DummyTest(name="bob"))
        return 123

    res = main1()  # pylint: disable=no-value-for-parameter
    assert isinstance(res, TestplanResult)
    assert res.decorated_value == 123
    assert res.run is True

    pdf_path = "mypdf.pdf"
    with argv_overridden("--pdf", pdf_path):

        @test_plan(name="MyPlan", port=800)
        def main2(plan, parser):
            args = parser.parse_args()

            assert args.verbose is False
            assert args.pdf_path == pdf_path
            assert plan.cfg.pdf_path == pdf_path
            plan.add(DummyTest(name="bob"))

        res = (
            main2()
        )  # pylint:disable=assignment-from-no-return,no-value-for-parameter
        assert isinstance(res, TestplanResult)
        assert res.decorated_value is None
        assert res.run is True


def test_testplan_runpath():
    """TODO."""

    def runpath_maker(obj):
        return "{sep}tmp{sep}custom".format(sep=os.sep)

    plan = Testplan(name="MyPlan", port=800, parse_cmdline=False)
    assert plan.runpath == default_runpath(plan._runnable)

    path = "/var/tmp/user"
    plan = TestplanMock(name="MyPlan", port=800, runpath=path)
    assert plan.runpath == path

    plan = TestplanMock(name="MyPlan", port=800, runpath=runpath_maker)
    assert plan.runpath == runpath_maker(plan._runnable)
