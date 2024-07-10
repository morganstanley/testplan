import time
import pytest
import re

from testplan import TestplanMock
from testplan.report import Status
from testplan.runnable import TestRunnerStatus
from testplan.runners.local import LocalRunner
from testplan.testing.base import ResourceHooks, Test
from testplan.testing.multitest.driver import Driver
from testplan.testing.multitest import MultiTest


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
        with self.result.report.timer.record("run"):
            time.sleep(0.5)  # 500ms for execution
            self.result.report.status_override = Status.PASSED

    def add_pre_resource_steps(self):
        self._add_step(lambda: self.result.report.timer.start("flag1"))
        self.make_runpath_dirs()
        super(DummyTest, self).add_pre_resource_steps()

    def add_pre_main_steps(self):
        super(DummyTest, self).add_pre_main_steps()
        self._add_step(lambda: self.result.report.timer.start("flag2"))

    def add_main_batch_steps(self):
        self._add_step(self.run_tests)

    def add_post_main_steps(self):
        self._add_step(lambda: self.result.report.timer.end("flag2"))
        super(DummyTest, self).add_post_main_steps()

    def add_post_resource_steps(self):
        super(DummyTest, self).add_post_resource_steps()
        self._add_step(lambda: self.result.report.timer.end("flag1"))


class MyRunner(LocalRunner):  # Start is async
    def __init__(self, name=None):
        self.name = name
        super(MyRunner, self).__init__()

    def uid(self):
        return self.name or super(MyRunner, self).uid()


class DummyFailingDriver(DummyDriver):
    def starting(self):
        time.sleep(0.3)
        raise Exception


class DummyTestWithFailingDriver(Test):
    def __init__(self, name, **options):
        super(DummyTestWithFailingDriver, self).__init__(
            name=name,
            environment=[DummyDriver("drv1"), DummyFailingDriver("drv2")],
            **options
        )

    def add_pre_resource_steps(self):
        self.make_runpath_dirs()
        super(DummyTestWithFailingDriver, self).add_pre_resource_steps()

    def run_tests(self):
        with self.result.report.timer.record("run"):
            time.sleep(0.5)  # 500ms for execution
            self.result.report.status_override = Status.PASSED
        super(DummyTestWithFailingDriver, self).add_pre_resource_steps()

    def add_main_batch_steps(self):
        self._add_step(self.run_tests)


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
    assert len(resources) == 0

    res = plan.run()

    assert len(resources) == 2 and "drv1" in resources and "drv2" in resources
    assert res.run is True

    test_report = res.report["Dummy"]
    assert test_report.name == "Dummy" and test_report.category == "dummytest"
    assert (
        test_report.timer.last(key="setup").elapsed > 0.4
    )  # 2 drivers startup
    assert (
        test_report.timer.last(key="teardown").elapsed > 0.2
    )  # 2 drivers teardown
    assert (
        test_report.timer.last(key="flag1").elapsed
        > test_report.timer.last(key="flag2").elapsed
        > test_report.timer.last(key="run").elapsed
        > 0.5
    )


def test_driver_no_report_information_without_flag():
    """Test that driver setup and teardown information is not in the report by default"""
    plan = TestplanMock(name="MyPlan")
    plan.add_resource(MyRunner(name="runner"))
    plan.schedule(DummyTest("Dummy"), resource="runner")
    res = plan.run()

    assert res.run is True
    report = res.report["Dummy"]
    assert (
        len(
            report.get_by_uids([ResourceHooks.ENVIRONMENT_START.value])
            .get_by_uids([ResourceHooks.STARTING.value])
            .entries
        )
        == 0
    )
    assert (
        len(
            report.get_by_uids([ResourceHooks.ENVIRONMENT_STOP.value])
            .get_by_uids([ResourceHooks.STOPPING.value])
            .entries
        )
        == 0
    )


def test_driver_report_information_with_flag():
    """Test that driver setup and teardown information is in the report when flag is enabled"""
    plan = TestplanMock(name="MyPlan", driver_info=True)
    plan.add_resource(MyRunner(name="runner"))
    plan.schedule(DummyTest("Dummy"), resource="runner")
    res = plan.run()

    assert res.run is True
    report = res.report["Dummy"]
    expected_drv1 = [
        "DummyDriver",
        "drv1",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
    ]
    expected_drv2 = [
        "DummyDriver",
        "drv2",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
    ]
    columns = [
        "Driver Class",
        "Driver Name",
        "Start Time (UTC)",
        "Stop Time (UTC)",
        "Duration(seconds)",
    ]

    driver_setup_report = (
        report.get_by_uids([ResourceHooks.ENVIRONMENT_START.value])
        .get_by_uids([ResourceHooks.STARTING.value])
        .entries[0]
    )
    assert driver_setup_report["columns"] == columns
    driver_setup_info = driver_setup_report["table"]
    assert len(driver_setup_info) == 2
    for i in range(len(expected_drv1)):
        assert re.search(expected_drv1[i], driver_setup_info[0][i])
        assert re.search(expected_drv2[i], driver_setup_info[1][i])
    assert 0.1 < driver_setup_info[0][-1] < 0.3
    assert 0.1 < driver_setup_info[1][-1] < 0.3

    driver_teardown_report = (
        report.get_by_uids([ResourceHooks.ENVIRONMENT_STOP.value])
        .get_by_uids([ResourceHooks.STOPPING.value])
        .entries[0]
    )
    assert driver_teardown_report["columns"] == columns
    driver_teardown_info = driver_teardown_report["table"]
    assert len(driver_teardown_info) == 2
    for i in range(len(expected_drv1)):
        assert re.search(expected_drv1[i], driver_teardown_info[1][i])
        assert re.search(expected_drv2[i], driver_teardown_info[0][i])
    assert 0 < driver_teardown_info[0][-1] < 0.2
    assert 0 < driver_teardown_info[1][-1] < 0.2


def test_driver_report_information_with_flag_when_driver_fails():
    """Test that report information when driver fails"""
    plan = TestplanMock(name="MyPlan", driver_info=True)
    plan.add_resource(MyRunner(name="runner"))
    plan.schedule(DummyTestWithFailingDriver("Dummy"), resource="runner")
    res = plan.run()

    assert res.run is True
    report = res.report["Dummy"]
    expected_drv1 = [
        "DummyDriver",
        "drv1",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
    ]
    expected_drv2 = [
        "DummyFailingDriver",
        "drv2",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
        r"\d{2}:\d{2}:\d{2}.\d{6}",
    ]
    columns = [
        "Driver Class",
        "Driver Name",
        "Start Time (UTC)",
        "Stop Time (UTC)",
        "Duration(seconds)",
    ]

    driver_setup_report = (
        report.get_by_uids([ResourceHooks.ENVIRONMENT_START.value])
        .get_by_uids([ResourceHooks.STARTING.value])
        .entries[0]
    )
    assert driver_setup_report["columns"] == columns
    driver_setup_info = driver_setup_report["table"]
    assert len(driver_setup_info) == 2
    for i in range(len(expected_drv1)):
        assert re.search(expected_drv1[i], driver_setup_info[0][i])
        if driver_setup_info[1][i] == None:
            # this is the stop time
            assert i + 1 == len(expected_drv1)
        else:
            assert re.search(expected_drv2[i], driver_setup_info[1][i])
    assert 0.1 < driver_setup_info[0][-1] < 0.3
    assert driver_setup_info[1][-1] == None

    driver_teardown_report = (
        report.get_by_uids([ResourceHooks.ENVIRONMENT_STOP.value])
        .get_by_uids([ResourceHooks.STOPPING.value])
        .entries[0]
    )
    assert driver_teardown_report["columns"] == columns
    driver_teardown_info = driver_teardown_report["table"]
    assert len(driver_teardown_info) == 2
    for i in range(len(expected_drv1)):
        assert re.search(expected_drv1[i], driver_teardown_info[1][i])
        assert re.search(expected_drv2[i], driver_teardown_info[0][i])
    assert 0 < driver_teardown_info[0][-1] < 0.2
    assert 0 < driver_teardown_info[1][-1] < 0.2
