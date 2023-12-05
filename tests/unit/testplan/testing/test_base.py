import time

from testplan import TestplanMock
from testplan.common.entity import Runnable
from testplan.report import Status
from testplan.runnable import TestRunnerStatus
from testplan.runners.local import LocalRunner
from testplan.testing.base import Test, TestResult
from testplan.testing.multitest.driver import Driver


class DummyDriver(Driver):
    def starting(self):
        time.sleep(0.2)  # 200ms for startup

    def stopping(self):
        time.sleep(0.1)  # 100ms for teardown

    def aborting(self):
        pass


class DummyTest(Test):
    def __init__(self, name, **options):
        super(DummyTest, self).__init__(
            name=name,
            environment=[DummyDriver("drv1"), DummyDriver("drv2")],
            **options
        )

    def run_tests(self):
        with self._result.report.timer.record("run"):
            time.sleep(0.5)  # 500ms for execution
            self._result.report.status_override = Status.PASSED

    def pre_resource_steps(self):
        self._add_step(lambda: self.result.report.timer.start("flag1"))
        super(DummyTest, self).pre_resource_steps()

    def pre_main_steps(self):
        super(DummyTest, self).pre_main_steps()
        self._add_step(lambda: self.result.report.timer.start("flag2"))

    def main_batch_steps(self):
        self._add_step(self.run_tests)

    def post_main_steps(self):
        self._add_step(lambda: self.result.report.timer.end("flag2"))
        super(DummyTest, self).post_main_steps()

    def post_resource_steps(self):
        super(DummyTest, self).post_resource_steps()
        self._add_step(lambda: self.result.report.timer.end("flag1"))


class MyRunner(LocalRunner):  # Start is async
    def __init__(self, name=None):
        self.name = name
        super(MyRunner, self).__init__()

    def uid(self):
        return self.name or super(MyRunner, self).uid()


def test_time_information():
    """TODO."""
    plan = TestplanMock(name="MyPlan")
    assert isinstance(plan.status, TestRunnerStatus)

    plan.add_resource(MyRunner(name="runner"))
    assert "runner" in plan.resources

    task_uid = plan.schedule(DummyTest("Dummy"), resource="runner")
    assert task_uid == "Dummy"
    assert len(plan.resources["runner"]._input) == 1
    resources = plan.resources["runner"]._input[task_uid].resources
    assert len(resources) == 2 and "drv1" in resources and "drv2" in resources

    res = plan.run()
    assert res.run is True

    test_report = res.report["Dummy"]
    assert test_report.name == "Dummy" and test_report.category == "dummytest"
    assert test_report.timer["setup"].elapsed > 0.4  # 2 drivers startup
    assert test_report.timer["teardown"].elapsed > 0.2  # 2 drivers teardown
    assert (
        test_report.timer["flag1"].elapsed
        > test_report.timer["flag2"].elapsed
        > test_report.timer["run"].elapsed
        > 0.5
    )
