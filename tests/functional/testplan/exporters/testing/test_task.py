"""Test the per-task assertions exporter."""

import threading
import time

import pytest

from testplan import Task, TestplanMock
from testplan.exporters.testing import JSONExporter, TaskExporter
from testplan.report import ReportCategories, TestGroupReport
from testplan.report.testing.schemas import TestReportSchema
from testplan.runners.pools.base import Pool as ThreadPool
from testplan.runners.pools.process import ProcessPool
from testplan.testing import multitest


@multitest.testsuite
class Alpha:
    def setup(self, env, result):
        result.log("alpha setup")

    @multitest.testcase
    def test_same_name(self, env, result):
        result.equal(1, 1, "alpha equality")

    @multitest.testcase(parameters=(1, 2))
    def test_param(self, env, result, arg):
        result.contain(arg, [1, 2])


@multitest.testsuite
class Beta:
    def setup(self, env, result):
        result.log("beta setup")

    @multitest.testcase
    def test_same_name(self, env, result):
        result.equal(2, 2, "beta equality")


@multitest.testsuite
class Plain:
    @multitest.testcase
    def test_pass(self, env, result):
        result.equal(1, 1, "plain equality")


@multitest.testsuite
class Failing:
    @multitest.testcase
    def test_fail(self, env, result):
        result.equal(1, 2, "failing assertion")


@multitest.testsuite
class Slow:
    @multitest.testcase
    def test_slow(self, env, result):
        result.log("before sleep")
        time.sleep(30)


def make_passing():
    return multitest.MultiTest(name="Passing", suites=[Alpha(), Beta()])


def make_plain():
    # No setup, synthesized entries survive filters
    return multitest.MultiTest(name="Plain", suites=[Plain()])


def make_failing():
    return multitest.MultiTest(name="Failing", suites=[Failing()])


class FakeTaskExporter(TaskExporter):
    """Records every upload in memory."""

    def __init__(self, fail_first=False, **options):
        super().__init__(**options)
        self.fail_first = fail_first
        self.uploads = []  # (test_uid, assertions, in_export)
        self.meta = None
        self.structure = None
        self._in_export = False

    def upload_assertions(self, test_uid, assertions):
        if self.fail_first:
            self.fail_first = False
            raise RuntimeError("first upload fails")
        self.uploads.append((test_uid, assertions, self._in_export))

    def upload_structure(self, meta, structure):
        self.meta = meta
        self.structure = structure
        return {"structure": len(structure)}

    def export(self, source, export_context):
        self._in_export = True
        return super().export(source, export_context)

    def uploaded(self, in_export):
        return [uid for uid, _, flag in self.uploads if flag is in_export]


def make_plan(runpath, exporter, **options):
    plan = TestplanMock(
        "plan", exporters=[exporter], runpath=runpath, **options
    )
    # Mock disables it, real runs reset uids
    plan.runnable._reset_report_uid = True
    return plan


def check_merged(plan, exporter):
    """Uploaded pieces rebuild the final report."""
    assert exporter.structure is not None
    structure_uids = [test["uid"] for test in exporter.structure]
    uploaded_uids = [uid for uid, _, _ in exporter.uploads]
    assert sorted(structure_uids) == sorted(uploaded_uids)

    assertions_map = {
        f"assertions_{uid}": assertions
        for uid, assertions, _ in exporter.uploads
    }
    merged = JSONExporter.merge_json_report(
        exporter.meta, exporter.structure, assertions_map
    )
    expected = TestReportSchema().dump(plan.report)
    assert merged["entries"] == expected["entries"]


@pytest.mark.parametrize("pool_type", [None, ThreadPool, ProcessPool])
def test_upload_per_task(runpath, pool_type):
    exporter = FakeTaskExporter()
    plan = make_plan(runpath, exporter)
    if pool_type is None:
        plan.add(make_passing())
        plan.add(make_failing())
    else:
        plan.add_resource(pool_type(name="MyPool", size=2))
        plan.schedule(task=Task(target=make_passing), resource="MyPool")
        plan.schedule(task=Task(target=make_failing), resource="MyPool")
    plan.run()

    assert len(exporter.uploaded(in_export=False)) == 2
    assert exporter.uploaded(in_export=True) == []
    # Suites share setup and case names
    assert sum(len(a) for _, a, _ in exporter.uploads) == 7
    check_merged(plan, exporter)


def test_upload_rerun_attempts(runpath):
    exporter = FakeTaskExporter()
    plan = make_plan(runpath, exporter)
    plan.add_resource(ThreadPool(name="MyPool", size=1))
    plan.schedule(
        task=Task(target=make_failing, rerun_limit=1), resource="MyPool"
    )
    plan.run()

    assert len(plan.report.entries) == 2
    assert plan.report.entries[1].category == ReportCategories.TASK_RERUN
    assert len(exporter.uploaded(in_export=False)) == 2
    check_merged(plan, exporter)


@pytest.mark.parametrize("flags", ["P", "p"])
def test_upload_with_filter(runpath, flags):
    exporter = FakeTaskExporter()
    plan = make_plan(runpath, exporter, reporting_exclude_filter=flags)
    plan.add(make_plain())
    plan.add(make_failing())
    plan.run()

    if flags == "P":
        # All-passed test is dropped entirely
        assert len(exporter.uploads) == 1
        assert [test["name"] for test in exporter.structure] == ["Failing"]
    else:
        # Passed cases kept with no assertions
        assert len(exporter.uploads) == 2
        plain = dict((uid, a) for uid, a, _ in exporter.uploads)[
            exporter.structure[0]["uid"]
        ]
        assert list(plain.values()) == [[]]
    check_merged(plan, exporter)


def test_failed_upload_retried(runpath):
    exporter = FakeTaskExporter(fail_first=True)
    plan = make_plan(runpath, exporter)
    plan.add(make_passing())
    plan.add(make_failing())
    plan.run()

    assert len(exporter.uploaded(in_export=False)) == 1
    assert len(exporter.uploaded(in_export=True)) == 1
    check_merged(plan, exporter)


def test_timeout_entry_in_export(runpath):
    exporter = FakeTaskExporter()
    plan = make_plan(runpath, exporter, timeout=5)
    plan.add(make_passing())
    plan.add(multitest.MultiTest(name="Slow", suites=[Slow()]))
    plan.run()

    names = {test["uid"]: test["name"] for test in exporter.structure}
    in_export = [names[uid] for uid in exporter.uploaded(in_export=True)]
    assert "Testplan timeout" in in_export
    assert "Passing" not in in_export
    check_merged(plan, exporter)


def test_stop_cancels_queued():
    started = threading.Event()
    release = threading.Event()

    class Blocking(FakeTaskExporter):
        def upload_assertions(self, test_uid, assertions):
            started.set()
            release.wait(10)
            super().upload_assertions(test_uid, assertions)

    exporter = Blocking()
    exporter.submit_task(TestGroupReport(name="First"))
    assert started.wait(10)
    exporter.submit_task(TestGroupReport(name="Second"))
    exporter.stop()
    release.set()
    exporter.drain()

    assert [uid for uid, _, _ in exporter.uploads] == ["First"]
