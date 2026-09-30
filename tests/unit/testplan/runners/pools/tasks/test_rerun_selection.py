"""Rerun selection must not combine or synthesize attempt report entries."""

import pytest

from testplan.testing.common import ALL_CASES
from testplan.report import (
    ReportCategories,
    Status,
    TestCaseReport,
    TestGroupReport,
)
from testplan.runners.pools.tasks.base import unresolved_selection


def multitest_report_with(**statuses):
    report = TestGroupReport(name="test", category=ReportCategories.MULTITEST)
    suite = TestGroupReport(
        name="suite", uid="suite", category=ReportCategories.TESTSUITE
    )
    for name, status in statuses.items():
        suite.append(
            TestCaseReport(name=name, uid=name, status_override=status)
        )
    report.append(suite)
    return report


@pytest.mark.parametrize(
    "statuses,planned,expected",
    [
        pytest.param(
            {"a": Status.PASSED},
            {"suite": ["a", "b"]},
            {"suite": ["b"]},
            id="missing-case",
        ),
        pytest.param(
            {"a": Status.PASSED},
            {"suite": ["a"], "absent": ["b"]},
            {"absent": ["b"]},
            id="missing-suite",
        ),
        pytest.param(
            {"a": Status.FAILED, "b": Status.SKIPPED},
            {"suite": ["a", "b"]},
            {"suite": ["a"]},
            id="failed-and-skipped",
        ),
        pytest.param(
            {"b": Status.SKIPPED},
            {"suite": ["b"]},
            {},
            id="only-skipped",
        ),
        pytest.param(
            {"a": Status.PASSED, "b": Status.FAILED},
            ALL_CASES,
            {"suite": ["b"]},
            id="infer-planned-cases-from-report",
        ),
        *[
            pytest.param(
                {"case": status},
                {"suite": ["case", "missing"]},
                ALL_CASES,
                id=f"no-terminal-case-{status.name.lower()}",
            )
            for status in (
                Status.FAILED,
                Status.ERROR,
                Status.UNKNOWN,
                Status.INCOMPLETE,
            )
        ],
    ],
)
def test_unresolved_selection_preserves_report(statuses, planned, expected):
    report = multitest_report_with(**statuses)
    original = report.serialize()
    selection = unresolved_selection(planned, report)
    if expected is ALL_CASES:
        assert selection is ALL_CASES
    else:
        assert selection == expected
    assert report.serialize() == original


@pytest.mark.parametrize(
    "planned,expected",
    [
        pytest.param(
            ALL_CASES,
            {"suite": ["check__value_2"]},
            id="infer-expanded-cases",
        ),
        pytest.param(
            {
                "suite": [
                    "plain",
                    "check__value_1",
                    "check__value_2",
                    "check__value_3",
                    "check__value_4",
                ]
            },
            {"suite": ["check__value_2", "check__value_4"]},
            id="failed-and-missing-expanded-cases",
        ),
    ],
)
def test_unresolved_selection_traverses_parametrization(planned, expected):
    report = multitest_report_with(plain=Status.PASSED)
    group = TestGroupReport(
        name="check", uid="check", category=ReportCategories.PARAMETRIZATION
    )
    for uid, status in (
        ("check__value_1", Status.PASSED),
        ("check__value_2", Status.FAILED),
        ("check__value_3", Status.SKIPPED),
    ):
        group.append(TestCaseReport(name=uid, uid=uid, status_override=status))
    report.entries[0].append(group)
    original = report.serialize()
    assert unresolved_selection(planned, report) == expected
    assert report.serialize() == original


@pytest.mark.parametrize(
    "category",
    [ReportCategories.GTEST, ReportCategories.PYTEST, "custom-test"],
)
@pytest.mark.parametrize("planned", [ALL_CASES, {"suite": ["done", "failed"]}])
def test_non_multitest_report_requires_full_rerun(category, planned):
    report = multitest_report_with(done=Status.PASSED, failed=Status.FAILED)
    assert unresolved_selection(planned, report) == {"suite": ["failed"]}
    report.category = category
    original = report.serialize()
    assert unresolved_selection(planned, report) is ALL_CASES
    assert report.serialize() == original


def test_lifecycle_failure_requires_full_rerun():
    report = multitest_report_with(a=Status.PASSED)
    report.entries[0].append(
        TestCaseReport(
            name="teardown",
            category=ReportCategories.SYNTHESIZED,
            status_override=Status.ERROR,
        )
    )
    assert unresolved_selection(ALL_CASES, report) is ALL_CASES


def test_strict_order_requires_full_rerun():
    report = multitest_report_with(done=Status.PASSED, failed=Status.FAILED)
    assert unresolved_selection(ALL_CASES, report) == {"suite": ["failed"]}
    report.entries[0].strict_order = True
    assert unresolved_selection(ALL_CASES, report) is ALL_CASES


def test_selective_task_serialization_keeps_execution_inputs():
    from testplan import Task

    task = Task(
        target="example.make_test",
        rerun_limit=3,
        rerun_entire_task=True,
        rerun_on_different_runner=True,
        part=(1, 3),
        case_selection={"suite": ["case_1"]},
    )
    task.rerun_cnt = 2
    task._failed_runners.add(("pool", "worker"))
    received = Task().loads(task.dumps())
    assert received.uid() == task.uid()
    assert received.case_selection == {"suite": ["case_1"]}
    assert received._part == (1, 3)
    assert received.rerun_limit == 0
    assert received.rerun_cnt == 0
    assert not received._failed_runners
    assert task.rerun_cnt == 2


def test_planned_case_metadata_roundtrip():
    from testplan import Task
    from testplan.runners.pools.tasks import TaskResult

    result = TaskResult(task=Task(), planned_cases={"suite": ["a"]})
    loaded = TaskResult().loads(result.dumps())
    assert loaded.planned_cases == {"suite": ["a"]}


def test_all_sentinel_survives_copy_and_transport():
    import copy

    from testplan import Task
    from testplan.common.serialization import deserialize, serialize
    from testplan.runners.pools.tasks import TaskResult

    assert copy.deepcopy(ALL_CASES) is ALL_CASES
    assert deserialize(serialize(ALL_CASES)) is ALL_CASES
    task = Task(case_selection={"suite": ALL_CASES})
    assert Task().loads(task.dumps()).case_selection["suite"] is ALL_CASES
    result = TaskResult(task=task)
    received = deserialize(serialize(result))
    assert received.planned_cases is ALL_CASES
    assert received.task.case_selection["suite"] is ALL_CASES
    assert TaskResult().loads(result.dumps()).planned_cases is ALL_CASES


def test_collect_planned_cases_expands_parameters_after_partitioning():
    from testplan import Task
    from testplan.runners.pools.tasks.base import collect_planned_cases
    from testplan.testing import filtering, ordering
    from testplan.testing.multitest import MultiTest, testcase, testsuite

    @testsuite
    class Cases:
        @testcase(parameters=(1, 2, 3))
        def check(self, env, result, value):
            result.true(value > 0)

    def factory():
        return MultiTest(
            name="test",
            suites=[Cases()],
            test_filter=filtering.Filter(),
            test_sorter=ordering.NoopSorter(),
        )

    task = Task(
        target=factory, part=(0, 2), case_selection={"Cases": ALL_CASES}
    )
    test = task.materialize()
    planned = collect_planned_cases(test)
    assert planned == {"Cases": ["check__value_1", "check__value_3"]}


def test_task_result_copies_planned_cases():
    from testplan.runners.pools.tasks import TaskResult

    planned = {"suite": ["case"]}
    result = TaskResult(planned_cases=planned)
    planned["suite"].clear()
    planned["other_suite"] = ["other_case"]
    assert result.planned_cases == {"suite": ["case"]}


@pytest.mark.parametrize(
    "terminal",
    [
        Status.PASSED,
        Status.XFAIL,
        Status.UNSTABLE,
        Status.SKIPPED,
        Status.XPASS,
    ],
)
@pytest.mark.parametrize("override_at", ["test", "suite"])
def test_group_override_preserves_terminal_cases(terminal, override_at):
    report = multitest_report_with(done=terminal, failed=Status.FAILED)
    group = report if override_at == "test" else report.entries[0]
    group.status_override = Status.INCOMPLETE
    original = report.serialize()
    assert unresolved_selection(
        {"suite": ["done", "failed", "missing"]}, report
    ) == {"suite": ["failed", "missing"]}
    assert report.serialize() == original


def test_empty_incomplete_report_requires_full_rerun():
    report = TestGroupReport(name="test", category=ReportCategories.MULTITEST)
    report.status_override = Status.INCOMPLETE
    assert unresolved_selection({"absent": ["case"]}, report) is ALL_CASES


@pytest.mark.parametrize(
    "status", [Status.PASSED, Status.XFAIL, Status.UNSTABLE, Status.SKIPPED]
)
def test_only_terminal_cases_do_not_require_rerun(status):
    report = multitest_report_with(done=status)
    report.status_override = status
    report.entries[0].status_override = status
    assert unresolved_selection({"suite": ["done"]}, report) == {}
