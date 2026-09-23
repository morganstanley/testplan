"""Rerun policies across thread and process workers."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from testplan import Task, TestplanMock
from testplan.testing.common import ALL_CASES
from testplan.runners.pools.base import Pool
from testplan.runners.pools.process import ProcessPool
from testplan.report import ReportCategories, Status
from testplan.testing.multitest import MultiTest, testcase, testsuite


@testsuite
class RerunCases:
    def __init__(self, log, always_fail=False, failures_before_pass=1):
        self.log = log
        self.always_fail = always_fail
        self.failures_before_pass = failures_before_pass

    def record(self, name):
        path = Path(self.log)
        previous = path.read_text().splitlines() if path.exists() else []
        with path.open("a") as stream:
            stream.write(name + "\n")
        return previous.count(name)

    @testcase
    def good(self, env, result):
        self.record("good")
        result.true(True)

    @testcase(parameters=(0, 1))
    def flaky(self, env, result, value):
        count = self.record(f"flaky{value}")
        result.true(
            value == 0
            or (count >= self.failures_before_pass and not self.always_fail)
        )


def make_rerun_test(log, always_fail=False, failures_before_pass=1):
    return MultiTest(
        name="rerun",
        suites=[RerunCases(log, always_fail, failures_before_pass)],
    )


@pytest.mark.parametrize("pool_type", [Pool, ProcessPool])
@pytest.mark.parametrize("entire", [True, False])
@pytest.mark.parametrize("failures", [1, 2])
def test_full_and_partial(tmp_path, pool_type, entire, failures):
    log = tmp_path / "calls"
    plan = TestplanMock(
        "rerun-plan",
        runpath=str(tmp_path / "run"),
        rerun_limit=2,
        **({"rerun_entire_task": True} if entire else {}),
    )
    pool = pool_type(name="pool", size=2)
    plan.add_resource(pool)
    task = Task(
        target=make_rerun_test,
        args=(str(log),),
        kwargs={"failures_before_pass": failures},
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert result.success
    assert result.report.status == Status.UNSTABLE
    assert task.rerun_cnt == failures
    calls = log.read_text().splitlines()
    assert calls.count("good") == (failures + 1 if entire else 1)
    assert calls.count("flaky0") == (failures + 1 if entire else 1)
    assert calls.count("flaky1") == failures + 1
    report = result.test_results[uid].report
    assert report.name == "rerun"
    assert report.uid == "rerun"
    assert report.status == Status.UNSTABLE
    assert report.category == ReportCategories.MULTITEST
    assert all(
        entry.status == Status.PASSED
        for entry in report.pre_order_iterate()
        if entry.category == ReportCategories.TESTCASE
    )
    count = 3 if entire else 1
    assert report.counter == {"passed": count, "failed": 0, "total": count}
    assert (
        sum(
            entry.category == ReportCategories.TESTCASE
            for entry in report.entries[0].pre_order_iterate()
        )
        == count
    )
    history = [entry for entry in result.report if entry is not report]
    assert [(entry.name, entry.status) for entry in history] == [
        (f"rerun => Run {attempt}", Status.UNSTABLE)
        for attempt in range(1, failures + 1)
    ]
    for attempt, entry in enumerate(history, start=1):
        assert entry.uid == f"rerun => Run {attempt}"
        assert entry.category == ReportCategories.TASK_RERUN
        total = 3 if entire or attempt == 1 else 1
        assert entry.counter == {
            "passed": total - 1,
            "failed": 1,
            "total": total,
        }
        cases = {
            case.uid: case.status
            for case in entry.pre_order_iterate()
            if case.category == ReportCategories.TESTCASE
        }
        expected = {"flaky__value_1": Status.FAILED}
        if total == 3:
            expected.update(good=Status.PASSED, flaky__value_0=Status.PASSED)
        assert cases == expected


@pytest.mark.parametrize("pool_type", [Pool, ProcessPool])
@pytest.mark.parametrize("size", [1, 2])
def test_exhaust_different_runners(tmp_path, pool_type, size):
    plan = TestplanMock("rerun-plan", runpath=str(tmp_path / "run"))
    pool = pool_type(name="pool", size=size)
    plan.add_resource(pool)
    log = tmp_path / "calls"
    task = Task(
        target=make_rerun_test,
        args=(str(log), True),
        rerun_limit=3,
        rerun_on_different_runner=True,
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert not result.success
    assert result.report.status == Status.FAILED
    final = result.test_results[uid].report
    assert final.name == "rerun"
    assert final.status == Status.FAILED
    history = [entry for entry in result.report if entry is not final]
    assert [(entry.name, entry.status) for entry in history] == [
        (f"rerun => Run {attempt}", Status.UNSTABLE)
        for attempt in range(1, size)
    ]
    assert task.rerun_cnt == size - 1
    assert len(task._failed_runners) == size
    assert log.read_text().splitlines().count("good") == 1
    assert log.read_text().splitlines().count("flaky1") == size


@pytest.mark.parametrize(
    "value",
    [
        None,
        "ALL_CASES",
        "all",
        [],
        {"s": "ALL_CASES"},
        {"s": None},
        {"s": [1]},
    ],
)
def test_invalid_selection(value):
    with pytest.raises(ValueError, match="case_selection"):
        Task(case_selection=value)


def test_task_policy_and_serialization():
    cfg = SimpleNamespace(
        rerun_limit=2,
        rerun_entire_task=False,
        rerun_on_different_runner=True,
    )
    task = Task(
        rerun_limit=0,
        rerun_entire_task=True,
        rerun_on_different_runner=False,
        case_selection={"s": ["c[1]"]},
    )
    task.resolve_rerun_policy(cfg)
    assert task.rerun_limit == 0
    assert task._rerun_entire_task is True
    assert task._rerun_on_different_runner is False
    loaded = Task().loads(task.dumps())
    assert loaded.case_selection == {"s": ["c[1]"]}
    assert loaded.rerun_limit == 0
    with pytest.raises(ValueError, match="only one"):
        Task(rerun=0, rerun_limit=1)


def test_selection_with_partition(tmp_path):
    log = tmp_path / "calls"
    plan = TestplanMock("subset", runpath=str(tmp_path / "run"))
    pool = Pool(name="pool", size=1)
    plan.add_resource(pool)
    task = Task(
        target=make_rerun_test,
        args=(str(log),),
        part=(0, 2),
        case_selection={"RerunCases": ALL_CASES},
    )
    plan.schedule(task=task, resource="pool")
    plan.run()
    assert log.read_text().splitlines() == ["good", "flaky1"]


def test_global_cli_and_task_precedence(monkeypatch, tmp_path):
    import importlib
    import sys
    from unittest.mock import patch

    module = importlib.import_module("testplan.base")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "plan.py",
            "--rerun-limit",
            "2",
            "--no-rerun-entire-task",
            "--rerun-on-different-runner",
        ],
    )
    captured = []

    @module.test_plan(
        name="config",
        runpath=str(tmp_path / "run"),
        rerun_limit=1,
        rerun_entire_task=True,
        rerun_on_different_runner=False,
    )
    def main(plan):
        pool = Pool(name="pool", size=1)
        plan.add_resource(pool)
        inherited = Task(target=make_rerun_test, args=("unused",))
        explicit = Task(
            target=make_rerun_test,
            args=("unused",),
            rerun_limit=0,
            rerun_entire_task=True,
            rerun_on_different_runner=False,
        )
        pool.add(inherited, inherited.uid())
        pool.add(explicit, explicit.uid())
        captured.extend([inherited, explicit])

    with patch.object(
        module.Testplan, "run", return_value=SimpleNamespace(success=True)
    ):
        main()
    inherited, explicit = captured
    assert (
        inherited.rerun_limit,
        inherited._rerun_entire_task,
        inherited._rerun_on_different_runner,
    ) == (2, False, True)
    assert (
        explicit.rerun_limit,
        explicit._rerun_entire_task,
        explicit._rerun_on_different_runner,
    ) == (0, True, False)


@pytest.mark.parametrize(
    "pattern,selection",
    [
        ("*:*:*", ["good", "*"]),
        ("*:*:good", ["good", "flaky__value_1"]),
    ],
    ids=["literal-case-ids", "intersect-existing-filter"],
)
def test_literal_case_selection(tmp_path, pattern, selection):
    from testplan.testing import filtering

    log = tmp_path / "calls"
    plan = TestplanMock(
        "subset",
        runpath=str(tmp_path / "run"),
        test_filter=filtering.Pattern(pattern),
    )
    pool = Pool(name="pool", size=1)
    plan.add_resource(pool)
    plan.schedule(
        task=Task(
            target=make_rerun_test,
            args=(str(log),),
            case_selection={"RerunCases": selection},
        ),
        resource="pool",
    )
    assert plan.run().success
    assert log.read_text().splitlines() == ["good"]


def test_localrunner_does_not_rerun(tmp_path):
    log = tmp_path / "calls"
    plan = TestplanMock(
        "local",
        runpath=str(tmp_path / "run"),
        rerun_limit=3,
        rerun_entire_task=False,
    )
    plan.add(make_rerun_test(str(log)))
    assert not plan.run().success
    assert log.read_text().splitlines().count("flaky1") == 1


@testsuite
class TeardownFailure(RerunCases):
    @testcase
    def good(self, env, result):
        self.record("good")
        result.true(True)

    @testcase
    def flaky(self, env, result):
        result.true(self.record("flaky") > 0)

    def teardown(self, env, result):
        result.true(self.record("teardown") > 0)


def make_teardown_test(log):
    return MultiTest(name="teardown", suites=[TeardownFailure(log)])


def test_partial_falls_back_after_teardown_failure(tmp_path):
    log = tmp_path / "calls"
    plan = TestplanMock("fallback", runpath=str(tmp_path / "run"))
    plan.add_resource(Pool(name="pool", size=1))
    task = Task(
        target=make_teardown_test,
        args=(str(log),),
        rerun_limit=2,
        rerun_entire_task=False,
    )
    plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert result.success
    assert result.report.unstable
    assert task.rerun_cnt == 1
    assert log.read_text().splitlines().count("good") == 2


@testsuite
class FailThenSkip:
    def __init__(self, log):
        self.log = Path(log)

    @testcase
    def flaky(self, env, result):
        if self.log.exists():
            result.skip("Condition changed")
        else:
            self.log.write_text("attempted")
            result.fail("Initial failure")


def make_fail_then_skip(log):
    return MultiTest(name="fail-then-skip", suites=[FailThenSkip(log)])


@pytest.mark.parametrize("entire", [False, True])
def test_skip_on_rerun_is_terminal(tmp_path, entire):
    plan = TestplanMock("skip-rerun", runpath=str(tmp_path / "run"))
    plan.add_resource(Pool(name="pool", size=1))
    task = Task(
        target=make_fail_then_skip,
        args=(str(tmp_path / "calls"),),
        rerun_limit=3,
        rerun_entire_task=entire,
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert task.rerun_cnt == 1
    assert result.test_results[uid].report.status == Status.SKIPPED


@pytest.mark.parametrize("entire", [False, True])
def test_full_fallback_keeps_current_task_selection(tmp_path, entire):
    log = tmp_path / "calls"
    plan = TestplanMock("rerun-selection", runpath=str(tmp_path / "run"))
    plan.add_resource(Pool(name="pool", size=1))
    original = {"RerunCases": ["good", "flaky__value_1"]}
    task = Task(
        target=make_rerun_test,
        args=(str(log), True),
        rerun_limit=2,
        rerun_entire_task=entire,
        case_selection=original,
    )
    plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert not result.success
    assert task.rerun_cnt == 2
    calls = log.read_text().splitlines()
    assert calls.count("good") == (3 if entire else 1)
    assert calls.count("flaky1") == 3
    assert "flaky0" not in calls
    assert task.case_selection == (
        original if entire else {"RerunCases": ["flaky__value_1"]}
    )


@testsuite
class StopEarlyCases:
    def __init__(self, log, error=False):
        self.log = log
        self.error = error

    record = RerunCases.record

    @testcase
    def first(self, env, result):
        self.record("first")
        result.true(True)

    @testcase
    def flaky(self, env, result):
        count = self.record("flaky")
        if self.error and count == 0:
            raise RuntimeError("First attempt fails")
        result.true(count > 0)

    @testcase
    def remaining(self, env, result):
        self.record("remaining")
        result.true(True)


@testsuite
class RemainingSuite:
    def __init__(self, log):
        self.log = log

    record = RerunCases.record

    @testcase
    def last(self, env, result):
        self.record("last")
        result.true(True)


def make_stop_early_test(log, strategy, error=False):
    from testplan.testing.ordering import NoopSorter

    return MultiTest(
        name="stop-early",
        suites=[StopEarlyCases(log, error), RemainingSuite(log)],
        test_sorter=NoopSorter(),
        **({"skip_strategy": strategy} if strategy else {}),
    )


@pytest.mark.parametrize("pool_type", [Pool, ProcessPool])
@pytest.mark.parametrize(
    "strategy",
    [
        "cases-on-failed",
        "suites-on-failed",
        "cases-on-error",
        "suites-on-error",
    ],
)
@pytest.mark.parametrize("global_strategy", [False, True])
@pytest.mark.parametrize("global_rerun", [False, True])
def test_rerun_after_skip_remaining(
    tmp_path, pool_type, strategy, global_strategy, global_rerun
):
    log = tmp_path / "calls"
    plan = TestplanMock(
        "skip-remaining",
        runpath=str(tmp_path / "run"),
        skip_strategy=strategy if global_strategy else None,
        rerun_limit=1 if global_rerun else 0,
    )
    plan.add_resource(pool_type(name="pool", size=1))
    task = Task(
        target=make_stop_early_test,
        args=(
            str(log),
            None if global_strategy else strategy,
            strategy.endswith("error"),
        ),
        rerun_limit=None if global_rerun else 1,
        rerun_entire_task=False,
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    final = result.test_results[uid].report
    histories = [entry for entry in result.report if entry is not final]
    assert result.success
    assert result.report.status == Status.UNSTABLE
    assert final.status == Status.UNSTABLE
    assert task.rerun_cnt == 1
    assert len(histories) == 1
    assert histories[0].status == Status.UNSTABLE
    initial_cases = {
        case.uid: case.status
        for case in histories[0].pre_order_iterate()
        if case.category == ReportCategories.TESTCASE
    }
    expected_initial = {
        "first": Status.PASSED,
        "flaky": Status.ERROR if strategy.endswith("error") else Status.FAILED,
    }
    if strategy.startswith("cases-"):
        expected_initial["last"] = Status.PASSED
    # Omitted cases have no report entry, including no SKIPPED placeholder.
    assert initial_cases == expected_initial
    expected_rerun = {"flaky", "remaining"}
    if strategy.startswith("suites-"):
        expected_rerun.add("last")
    assert {
        case.uid: case.status
        for case in final.pre_order_iterate()
        if case.category == ReportCategories.TESTCASE
    } == {case: Status.PASSED for case in expected_rerun}
    calls = log.read_text().splitlines()
    assert calls.count("first") == 1
    assert calls.count("flaky") == 2
    assert calls.count("remaining") == 1
    assert calls.count("last") == 1


@pytest.mark.parametrize("pool_type", [Pool, ProcessPool])
@pytest.mark.parametrize("strategy", ["tests-on-failed", "tests-on-error"])
def test_skip_remaining_tests_disables_rerun(tmp_path, pool_type, strategy):
    log = tmp_path / "calls"
    plan = TestplanMock(
        "skip-tests",
        runpath=str(tmp_path / "run"),
        skip_strategy=strategy,
        rerun_limit=1,
    )
    plan.add_resource(pool_type(name="pool", size=1))
    task = Task(
        target=make_stop_early_test,
        args=(str(log), None, strategy.endswith("error")),
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert not result.success
    assert task.rerun_cnt == 0
    final = result.test_results[uid].report
    assert list(result.report) == [final]
    assert final.status == (
        Status.ERROR if strategy.endswith("error") else Status.FAILED
    )
    assert log.read_text().splitlines() == ["first", "flaky"]


def make_pytest_rerun_test(target):
    from testplan.testing.py_test import PyTest

    root = str(Path(target).parent)
    return PyTest(
        name="pytest-rerun",
        target=target,
        extra_args=[
            "-c",
            str(Path(root) / "pytest.ini"),
            "--rootdir",
            root,
            "--confcutdir",
            root,
            "--import-mode=importlib",
        ],
    )


@pytest.mark.parametrize("pool_type", [Pool, ProcessPool])
@pytest.mark.parametrize("entire", [False, True])
def test_pytest_task_reruns_entire_target(tmp_path, pool_type, entire):
    # Nested pytest caches imported modules across thread-pool scenarios.
    target = tmp_path / f"test_{tmp_path.name}.py"
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    target.write_text(
        "from pathlib import Path\n"
        "\n"
        "def record(name):\n"
        "    log = Path(__file__).with_name('calls')\n"
        "    previous = log.read_text().splitlines() if log.exists() else []\n"
        "    with log.open('a') as stream:\n"
        "        stream.write(name + '\\n')\n"
        "    return previous.count(name)\n"
        "\n"
        "def test_good():\n"
        "    record('good')\n"
        "\n"
        "def test_flaky():\n"
        "    assert record('flaky') > 0\n"
    )
    plan = TestplanMock("pytest-task", runpath=str(tmp_path / "run"))
    plan.add_resource(pool_type(name="pool", size=1))
    task = Task(
        target=make_pytest_rerun_test,
        args=(str(target),),
        rerun_limit=1,
        rerun_entire_task=entire,
    )
    uid = plan.schedule(task=task, resource="pool")
    result = plan.run()
    assert result.success
    assert result.report.status == Status.UNSTABLE
    assert task.rerun_cnt == 1
    # Non-MultiTest targets rerun fully even when partial mode is requested.
    assert (tmp_path / "calls").read_text().splitlines() == [
        "good",
        "flaky",
        "good",
        "flaky",
    ]
    final = result.test_results[uid].report
    assert final.name == "pytest-rerun"
    assert final.category == ReportCategories.PYTEST
    assert final.status == Status.UNSTABLE
    assert final.counter == {"passed": 2, "failed": 0, "total": 2}
    history = [entry for entry in result.report if entry is not final]
    assert len(history) == 1
    assert history[0].name == "pytest-rerun => Run 1"
    assert history[0].category == ReportCategories.TASK_RERUN
    assert history[0].status == Status.UNSTABLE
    assert history[0].counter == {"passed": 1, "failed": 1, "total": 2}
    for report, flaky_status in (
        (history[0], Status.FAILED),
        (final, Status.PASSED),
    ):
        assert {
            case.uid: case.status
            for case in report.pre_order_iterate()
            if case.category == ReportCategories.TESTCASE
        } == {"test_good": Status.PASSED, "test_flaky": flaky_status}
