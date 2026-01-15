import re
from typing import List, Optional, Dict

from opentelemetry.sdk._logs import LogData
from opentelemetry.sdk.trace import Span

from testplan import TestplanMock
from testplan.common.utils.observability import TraceLevel, otel_logging
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


# Set outputstyle so the result.log/equal get logged out
OUTPUT_STYLE = Style(StyleEnum.ASSERTION, StyleEnum.ASSERTION)


# ANSI escape code pattern for stripping color codes
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE_PATTERN.sub("", text)


def find_span(spans, name: str) -> Optional[Span]:
    """Helper to find a span by name."""
    for span in spans:
        if span.name == name:
            return span
    return None


def group_logs_by_span(
    logs: List[LogData], span_map: Dict[str, Span]
) -> Dict[str, List[LogData]]:
    """
    Groups logs by their associated span.
    """
    logs_by_span = {name: [] for name in span_map.keys()}

    for log in logs:
        for span_name, span in span_map.items():
            if log.log_record.span_id == span.context.span_id:
                logs_by_span[span_name].append(log)
                break

    return logs_by_span


def assert_span_exists(spans: List[Span], span_name: str) -> Span:
    span = find_span(spans, span_name)
    assert span is not None
    return span


def assert_span_not_exists(spans: List[Span], span_name: str):
    span = find_span(spans, span_name)
    assert span is None


def assert_messages_in_logs(logs: List[LogData], expected_messages: List[str]):
    messages = [strip_ansi_codes(log.log_record.body) for log in logs]
    for expected_msg in expected_messages:
        assert any(expected_msg in msg for msg in messages)


def assert_messages_not_in_logs(
    logs: List[LogData], unexpected_messages: List[str]
):
    messages = [strip_ansi_codes(log.log_record.body) for log in logs]
    for unexpected_msg in unexpected_messages:
        assert not any(unexpected_msg in msg for msg in messages)


def filter_logs_by_trace_id(
    logs: List[LogData], expected_trace_id
) -> List[LogData]:
    """
    Filter logs to only include those matching the expected trace_id.

    This is necessary because otel_logging is a singleton that captures all logs
    globally, including logs from concurrent threads.
    """
    return [
        log for log in logs if log.log_record.trace_id == expected_trace_id
    ]


@testsuite
class MySuite:
    @testcase
    def test_one(self, env, result):
        result.log("Test Output")
        result.equal(1, 1)


@testsuite
class AnotherSuite:
    @testcase
    def test_two(self, env, result):
        result.log("Another test output")
        result.equal(2, 2)

    @testcase
    def test_three(self, env, result):
        result.log("Third test output")
        result.equal(3, 3)


@testsuite
class FailingSuite:
    @testcase
    def successful_case(self, env, result):
        result.equal(1, 1)

    @testcase
    def failing_case(self, env, result):
        result.equal(1, 2)


def test_logging_disabled_by_default(test_log_exporter):
    """
    Tests that no logs are captured when logging is not explicitly enabled.
    """
    mockplan = TestplanMock(name="MockPlan")
    assert otel_logging._logging_enabled is False

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    logs = test_log_exporter.get_finished_logs()
    assert len(logs) == 0, "Expected no logs when logging disabled by default"


def test_logs_at_testcase_level(test_log_exporter, test_exporter):
    """
    Tests that logs contain correct trace_id and span_id that match testcase spans,
    and that log content matches expected test output.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    span_map = {
        "test_one": assert_span_exists(spans, "test_one"),
        "MySuite": assert_span_exists(spans, "MySuite"),
        "MyMultitest": assert_span_exists(spans, "MyMultitest"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    assert len(logs_by_span["test_one"]) == 2
    assert len(logs_by_span["MySuite"]) > 0
    assert len(logs_by_span["MyMultitest"]) > 0
    assert len(logs_by_span["MockPlan"]) > 0

    assert_messages_in_logs(
        logs_by_span["test_one"],
        ["Test Output", "1 == 1 - Pass"],
    )
    assert_messages_in_logs(
        logs_by_span["MySuite"],
        [
            "[test_one] ---------------- testcase start ----------------",
            "[test_one] -> Passed",
            "[test_one] ----------------- testcase end -----------------",
        ],
    )
    assert_messages_in_logs(
        logs_by_span["MyMultitest"],
        [
            "Executing step of MultiTest[MyMultitest] - run_tests",
            "Finished step of MultiTest[MyMultitest] - run_tests",
        ],
    )
    assert_messages_in_logs(
        logs_by_span["MockPlan"],
        ["[MockPlan] -> Passed"],
    )


def test_logs_at_testsuite_level(test_log_exporter, test_exporter):
    """
    Tests that logs are captured at testsuite level when trace level is TESTSUITE.
    At this level, there are no testcase spans, only testsuite and above.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTSUITE,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    assert_span_not_exists(spans, "test_one")

    span_map = {
        "MySuite": assert_span_exists(spans, "MySuite"),
        "MyMultitest": assert_span_exists(spans, "MyMultitest"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    for span_name in span_map:
        assert len(logs_by_span[span_name]) > 0

    assert_messages_in_logs(
        logs_by_span["MySuite"],
        [
            "Test Output",
            "1 == 1 - Pass",
            "[test_one] ---------------- testcase start ----------------",
            "[test_one] -> Passed",
            "[test_one] ----------------- testcase end -----------------",
        ],
    )
    assert_messages_in_logs(
        logs_by_span["MyMultitest"],
        [
            "Executing step of MultiTest[MyMultitest] - run_tests",
            "Finished step of MultiTest[MyMultitest] - run_tests",
        ],
    )
    assert_messages_in_logs(
        logs_by_span["MockPlan"],
        ["[MockPlan] -> Passed"],
    )


def test_logs_at_test_level(test_log_exporter, test_exporter):
    """
    Tests that logs are captured at multitest level when trace level is TEST.
    At this level, there are no testcase or testsuite spans, only multitest and above.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TEST,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    assert_span_not_exists(spans, "test_one")
    assert_span_not_exists(spans, "MySuite")

    span_map = {
        "MyMultitest": assert_span_exists(spans, "MyMultitest"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    for span_name in span_map:
        assert len(logs_by_span[span_name]) > 0

    assert_messages_in_logs(
        logs_by_span["MyMultitest"],
        [
            "Test Output",
            "1 == 1 - Pass",
            "[test_one] ---------------- testcase start ----------------",
            "[test_one] -> Passed",
            "[test_one] ----------------- testcase end -----------------",
            "Executing step of MultiTest[MyMultitest] - run_tests",
            "Finished step of MultiTest[MyMultitest] - run_tests",
        ],
    )

    assert_messages_in_logs(
        logs_by_span["MockPlan"],
        ["[MockPlan] -> Passed"],
    )


def test_logs_at_testplan_level(test_log_exporter, test_exporter):
    """
    Tests that logs are captured at testplan level when trace level is PLAN.
    At this level, there are no testcase, testsuite, or multitest spans, only testplan span.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.PLAN,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    assert_span_not_exists(spans, "test_one")
    assert_span_not_exists(spans, "MySuite")
    assert_span_not_exists(spans, "MyMultitest")

    testplan_span = assert_span_exists(spans, "MockPlan")
    span_map = {"MockPlan": testplan_span}

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    assert len(logs_by_span["MockPlan"]) > 0

    assert_messages_in_logs(
        logs_by_span["MockPlan"],
        [
            "Test Output",
            "1 == 1 - Pass",
            "[test_one] ---------------- testcase start ----------------",
            "[test_one] -> Passed",
            "Executing step of MultiTest[MyMultitest] - run_tests",
            "Finished step of MultiTest[MyMultitest] - run_tests",
        ],
    )


def test_logs_with_multiple_suites(test_log_exporter, test_exporter):
    """
    Tests that logs are properly separated and attributed when multiple
    test suites run in one MultiTest.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[MySuite(), AnotherSuite()])
    )
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    span_map = {
        "MySuite": assert_span_exists(spans, "MySuite"),
        "AnotherSuite": assert_span_exists(spans, "AnotherSuite"),
        "test_one": assert_span_exists(spans, "test_one"),
        "test_two": assert_span_exists(spans, "test_two"),
        "test_three": assert_span_exists(spans, "test_three"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    for span_name in span_map:
        assert len(logs_by_span[span_name]) > 0

    assert_messages_in_logs(
        logs_by_span["test_one"],
        ["Test Output", "1 == 1 - Pass"],
    )
    assert_messages_in_logs(
        logs_by_span["test_two"],
        ["Another test output", "2 == 2 - Pass"],
    )
    assert_messages_in_logs(
        logs_by_span["test_three"],
        ["Third test output", "3 == 3 - Pass"],
    )

    # Verify suite logs contain only their own testcases
    assert_messages_in_logs(
        logs_by_span["MySuite"],
        ["[test_one]"],
    )
    assert_messages_not_in_logs(
        logs_by_span["MySuite"],
        ["[test_two]", "[test_three]"],
    )

    assert_messages_in_logs(
        logs_by_span["AnotherSuite"],
        ["[test_two]", "[test_three]"],
    )
    assert_messages_not_in_logs(
        logs_by_span["AnotherSuite"],
        ["[test_one]"],
    )


def test_logs_with_multiple_multitests(test_log_exporter, test_exporter):
    """
    Tests that logs are properly separated when multiple MultiTests
    run in one TestPlan.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="FirstMultitest", suites=[MySuite()]))
    mockplan.add(MultiTest(name="SecondMultitest", suites=[AnotherSuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    span_map = {
        "FirstMultitest": assert_span_exists(spans, "FirstMultitest"),
        "SecondMultitest": assert_span_exists(spans, "SecondMultitest"),
        "MySuite": assert_span_exists(spans, "MySuite"),
        "AnotherSuite": assert_span_exists(spans, "AnotherSuite"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )

    assert (
        span_map["FirstMultitest"].context.span_id
        != span_map["SecondMultitest"].context.span_id
    )
    assert (
        span_map["MySuite"].context.span_id
        != span_map["AnotherSuite"].context.span_id
    )

    logs_by_span = group_logs_by_span(logs, span_map)

    for span_name in span_map:
        assert len(logs_by_span[span_name]) > 0

    # Verify multitest logs contain only their own names
    assert_messages_in_logs(
        logs_by_span["FirstMultitest"],
        ["FirstMultitest"],
    )
    assert_messages_not_in_logs(
        logs_by_span["FirstMultitest"],
        ["SecondMultitest"],
    )

    assert_messages_in_logs(
        logs_by_span["SecondMultitest"],
        ["SecondMultitest"],
    )
    assert_messages_not_in_logs(
        logs_by_span["SecondMultitest"],
        ["FirstMultitest"],
    )

    # Verify suite-specific logs
    assert_messages_in_logs(
        logs_by_span["MySuite"],
        ["[test_one]"],
    )

    # AnotherSuite has test_two and test_three
    anothersuite_messages = [
        strip_ansi_codes(log.log_record.body)
        for log in logs_by_span["AnotherSuite"]
    ]
    assert any(
        "[test_two]" in msg or "[test_three]" in msg
        for msg in anothersuite_messages
    )


def test_logs_with_failing_tests(test_log_exporter, test_exporter):
    """
    Tests that assertion failures are properly logged with failure messages.
    """
    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_logs=True,
        stdout_style=OUTPUT_STYLE,
    )

    mockplan.add(MultiTest(name="MyMultitest", suites=[FailingSuite()]))
    mockplan.run()

    all_logs = test_log_exporter.get_finished_logs()
    spans = test_exporter.get_finished_spans()

    span_map = {
        "successful_case": assert_span_exists(spans, "successful_case"),
        "failing_case": assert_span_exists(spans, "failing_case"),
        "FailingSuite": assert_span_exists(spans, "FailingSuite"),
        "MockPlan": assert_span_exists(spans, "MockPlan"),
    }

    logs = filter_logs_by_trace_id(
        all_logs, span_map["MockPlan"].context.trace_id
    )
    logs_by_span = group_logs_by_span(logs, span_map)

    for span_name in span_map:
        assert len(logs_by_span[span_name]) > 0

    assert_messages_in_logs(
        logs_by_span["successful_case"],
        ["1 == 1 - Pass"],
    )

    failing_messages = [
        strip_ansi_codes(log.log_record.body)
        for log in logs_by_span["failing_case"]
    ]
    assert any("1 == 2" in msg and "Fail" in msg for msg in failing_messages)

    assert_messages_in_logs(
        logs_by_span["FailingSuite"],
        ["[successful_case] -> Passed", "[failing_case] -> Failed"],
    )
