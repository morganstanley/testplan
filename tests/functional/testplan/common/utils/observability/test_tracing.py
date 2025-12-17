from typing import Optional
import pytest

from opentelemetry.sdk.trace import Span

from testplan import TestplanMock
from testplan.common.utils.observability import TraceLevel, tracing
from testplan.testing.multitest import MultiTest, testsuite, testcase


def find_span(spans: list[Span], name: str) -> Optional[Span]:
    """Helper to find a span by name."""
    for span in spans:
        if span.name == name:
            return span
    return None


@testsuite
class MySuite:
    @testcase
    def test_one(self, env, result):
        result.equal(1, 1)

    @testcase
    def test_two(self, env, result):
        result.equal(2, 2)


@testsuite
class FailingSuite:
    @testcase
    def successful_case(self, env, result):
        result.equal(1, 1)

    @testcase
    def failing_case(self, env, result):
        result.equal(1, 2)


@testsuite
class UserSpanSuite:
    """Suite demonstrating user-created spans."""

    @testcase
    def test_with_context_manager_span(self, env, result):
        """Test using context manager span."""
        with tracing.span("user_operation", operation_type="custom") as span:
            result.equal(1, 1)

    @testcase
    def test_with_manual_span(self, env, result):
        """Test using manual start/end span."""
        span = tracing.start_span("manual_operation", method="POST")
        try:
            result.equal(2, 2)
        finally:
            tracing.end_span(span)

    @testcase
    def test_with_nested_spans(self, env, result):
        """Test with nested user spans."""
        with tracing.span("parent_op") as parent:
            result.log("Parent operation")
            with tracing.span("child_op") as child:
                result.equal(1, 1)

    @testcase
    def test_with_span_attributes(self, env, result):
        """Test setting span attributes."""
        with tracing.span("attributed_op") as span:
            result.equal(1, 1)
            tracing.set_span_attrs(
                span=span,
                records_processed=100,
                success_rate=0.95,
            )

    @testcase
    def test_with_failing_user_span(self, env, result):
        """Test marking user span as failed."""
        with tracing.span("failing_user_op") as span:
            is_valid = False
            if not is_valid:
                tracing.set_span_as_failed(
                    span=span, description="User validation failed"
                )
                result.fail("User validation failed")


@testsuite
class MultiStepSpanSuite:
    """Suite demonstrating spans across multiple test cases."""

    span = None

    @testcase
    def step_1_start_workflow(self, env, result):
        """Start a multi-step workflow span."""
        self.span = tracing.start_span(
            "workflow", workflow_id="wf-001", total_steps=2
        )
        result.equal(1, 1)

    @testcase
    def step_2_end_workflow(self, env, result):
        """End the multi-step workflow span."""
        result.equal(2, 2)
        tracing.end_span(self.span)


@testsuite
class ConditionalSpanSuite:
    """Suite demonstrating conditional span creation."""

    @testcase
    def test_with_conditional_span_true(self, env, result):
        """Test conditional span when condition is True."""
        with tracing.conditional_span(
            "conditional_op", condition=True, op_type="test"
        ) as span:
            result.equal(1, 1)

    @testcase
    def test_with_conditional_span_false(self, env, result):
        """Test conditional span when condition is False."""
        with tracing.conditional_span(
            "skipped_op", condition=False, op_type="test"
        ) as span:
            result.equal(1, 1)


@testsuite
class DecoratorSpanSuite:
    """Suite demonstrating the trace decorator."""

    @testcase
    def test_decorated_method(self, env, result):
        """Test using the trace decorator."""
        self._decorated_operation(result)

    @tracing.trace
    def _decorated_operation(self, result):
        """A decorated helper method."""
        result.equal(1, 1)


def test_tracing_disabled_by_default(test_exporter):
    """
    Tests that no spans are created when tracing is not explicitly enabled.
    This is the default behavior.
    """
    mockplan = TestplanMock(name="MockPlan")
    assert tracing._tracing_enabled is False

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 0, (
        "Expected no spans when tracing disabled by default"
    )


def test_otel_traces_flag_set_to_Plan(test_exporter):
    """
    Tests that when otel_traces is set to "Plan", only a single span
    is created for the whole Testplan with no child spans.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.PLAN)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    # root Testplan
    assert len(spans) == 1

    tp_span = find_span(spans, "MockPlan")
    assert tp_span is not None


def test_otel_traces_flag_set_to_Test(test_exporter):
    """
    Tests that when otel_traces is set to "Test", only a single span
    is created for the MultiTest with no child spans.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TEST)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    # root Testplan + MultiTest
    assert len(spans) == 2

    tp_span = find_span(spans, "MockPlan")
    assert tp_span is not None
    mt_span = find_span(spans, "MyMultitest")
    assert mt_span is not None
    assert mt_span.parent.span_id == tp_span.context.span_id


def test_otel_trace_flag_set_to_TestSuite(test_exporter):
    """
    Tests that when otel_trace is set to "TestSuite", spans are created
    for the MultiTest and each TestSuite, but not for individual test cases.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTSUITE)
    assert tracing._tracing_enabled

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[MySuite(), FailingSuite()])
    )
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    # root Testplan + MultiTest + Env Start/Stop + 2 TestSuites
    assert len(spans) == 6

    tp_span = find_span(spans, "MockPlan")
    assert tp_span is not None
    mt_span = find_span(spans, "MyMultitest")
    assert mt_span is not None
    assert mt_span.parent.span_id == tp_span.context.span_id

    env_start_span = find_span(spans, "Environment Start")
    env_stop_span = find_span(spans, "Environment Stop")
    assert env_start_span is not None
    assert env_stop_span is not None
    assert env_start_span.parent.span_id == mt_span.context.span_id
    assert env_stop_span.parent.span_id == mt_span.context.span_id

    mysuite_span = find_span(spans, "MySuite")
    failing_suite_span = find_span(spans, "FailingSuite")
    assert mysuite_span is not None
    assert failing_suite_span is not None
    assert mysuite_span.parent.span_id == mt_span.context.span_id
    assert failing_suite_span.parent.span_id == mt_span.context.span_id


def test_otel_trace_flag_set_to_TestCase(test_exporter):
    """
    Tests that when otel_trace is set to "TestCase", spans are created
    for everything: MultiTest, TestSuites, and individual test cases.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[MySuite(), FailingSuite()])
    )
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    # root Testplan + MultiTest + Env Start/Stop + 2 TestSuites + 4 TestCases
    assert len(spans) == 10

    tp_span = find_span(spans, "MockPlan")
    assert tp_span is not None
    mt_span = find_span(spans, "MyMultitest")
    assert mt_span is not None
    assert mt_span.parent.span_id == tp_span.context.span_id

    env_start_span = find_span(spans, "Environment Start")
    env_stop_span = find_span(spans, "Environment Stop")
    assert env_start_span is not None
    assert env_stop_span is not None
    assert env_start_span.parent.span_id == mt_span.context.span_id
    assert env_stop_span.parent.span_id == mt_span.context.span_id

    mysuite_span = find_span(spans, "MySuite")
    failing_suite_span = find_span(spans, "FailingSuite")
    assert mysuite_span is not None
    assert failing_suite_span is not None
    assert mysuite_span.parent.span_id == mt_span.context.span_id
    assert failing_suite_span.parent.span_id == mt_span.context.span_id

    test_one_span = find_span(spans, "test_one")
    test_two_span = find_span(spans, "test_two")
    assert test_one_span is not None
    assert test_two_span is not None
    assert test_one_span.parent.span_id == mysuite_span.context.span_id
    assert test_two_span.parent.span_id == mysuite_span.context.span_id

    successful_case_span = find_span(spans, "successful_case")
    failing_case_span = find_span(spans, "failing_case")
    assert successful_case_span is not None
    assert failing_case_span is not None
    assert (
        successful_case_span.parent.span_id
        == failing_suite_span.context.span_id
    )
    assert (
        failing_case_span.parent.span_id == failing_suite_span.context.span_id
    )


def test_successful_and_failing_case_status(test_exporter):
    """
    Tests that a successful testcase has a span with OK status, and
    a failing testcase has a span with ERROR status (when TestCase tracing is enabled).
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[FailingSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    tp_span = find_span(spans, "MockPlan")
    mt_span = find_span(spans, "MyMultitest")
    successful_case_span = find_span(spans, "successful_case")
    failing_case_span = find_span(spans, "failing_case")

    assert successful_case_span.status.is_ok
    assert not failing_case_span.status.is_ok
    assert failing_case_span.status.status_code.name == "ERROR"
    assert not mt_span.status.is_ok
    assert mt_span.status.status_code.name == "ERROR"
    assert not tp_span.status.is_ok
    assert tp_span.status.status_code.name == "ERROR"


def test_multiple_multitests(test_exporter):
    """
    Tests span hierarchy when multiple MultiTests are added to the same plan.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TEST)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MultiTest1", suites=[MySuite()]))
    mockplan.add(MultiTest(name="MultiTest2", suites=[FailingSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    # root Testplan + 2 MultiTests
    assert len(spans) == 3

    tp_span = find_span(spans, "MockPlan")
    mt1_span = find_span(spans, "MultiTest1")
    mt2_span = find_span(spans, "MultiTest2")

    assert tp_span is not None
    assert mt1_span is not None
    assert mt2_span is not None
    assert mt1_span.parent.span_id == tp_span.context.span_id
    assert mt2_span.parent.span_id == tp_span.context.span_id


def test_user_created_spans_with_context_manager(test_exporter):
    """
    Tests user-created spans using context manager.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[UserSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()
    user_op_span = find_span(spans, "user_operation")
    test_case_span = find_span(spans, "test_with_context_manager_span")
    assert user_op_span is not None
    assert test_case_span is not None

    assert user_op_span.parent.span_id == test_case_span.context.span_id
    assert user_op_span.attributes.get("operation_type") == "custom"


def test_user_created_spans_with_manual_start_end(test_exporter):
    """
    Tests user-created spans using manual start/end.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[UserSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    manual_op_span = find_span(spans, "manual_operation")
    test_case_span = find_span(spans, "test_with_manual_span")

    assert manual_op_span is not None
    assert test_case_span is not None
    assert manual_op_span.parent.span_id == test_case_span.context.span_id
    assert manual_op_span.attributes.get("method") == "POST"


def test_user_created_nested_spans(test_exporter):
    """
    Tests nested user-created spans.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[UserSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    parent_op_span = find_span(spans, "parent_op")
    child_op_span = find_span(spans, "child_op")
    test_case_span = find_span(spans, "test_with_nested_spans")
    assert parent_op_span is not None
    assert child_op_span is not None
    assert test_case_span is not None
    assert parent_op_span.parent.span_id == test_case_span.context.span_id
    assert child_op_span.parent.span_id == parent_op_span.context.span_id


def test_user_span_with_custom_attributes(test_exporter):
    """
    Tests setting custom attributes on user-created spans.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[UserSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    attributed_span = find_span(spans, "attributed_op")
    assert attributed_span is not None

    # Verify custom attributes were set
    assert attributed_span.attributes.get("records_processed") == 100
    assert attributed_span.attributes.get("success_rate") == 0.95


def test_user_span_marked_as_failed(test_exporter):
    """
    Tests that user-created spans can be marked as failed.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[UserSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    failing_user_span = find_span(spans, "failing_user_op")
    assert failing_user_span is not None

    # Verify the user span is marked as failed
    assert not failing_user_span.status.is_ok
    assert failing_user_span.status.status_code.name == "ERROR"
    assert "User validation failed" in failing_user_span.status.description


def test_multi_step_workflow_span(test_exporter):
    """
    Tests spans that span across multiple test cases.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MultiStepSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    workflow_span = find_span(spans, "workflow")
    step1_span = find_span(spans, "step_1_start_workflow")
    step2_span = find_span(spans, "step_2_end_workflow")

    assert workflow_span is not None
    assert step1_span is not None
    assert step2_span is not None

    # Workflow span should be nested under step 1 (where it was started)
    assert workflow_span.parent.span_id == step1_span.context.span_id

    # Verify workflow attributes
    assert workflow_span.attributes.get("workflow_id") == "wf-001"
    assert workflow_span.attributes.get("total_steps") == 2


def test_empty_testplan_with_tracing(test_exporter):
    """
    Test that no root span is created for empty test plan.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TEST)
    mockplan.run()

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 0, "No root span should be created for empty plan"


def test_otel_traceparent_flag(test_exporter):
    """
    Tests that otel_traceparent is properly injected as root context
    for distributed tracing.
    """
    test_traceparent = (
        "00-a4f7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    )

    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_traceparent=test_traceparent,
    )
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    expected_trace_id = test_traceparent.split("-")[1]
    for span in spans:
        span_trace_id = format(span.context.trace_id, "x")
        assert span_trace_id == expected_trace_id


def test_otel_traceparent_flag_with_only_valid_traceid(test_exporter):
    """
    Tests that otel_traceparent is properly injected as root context
    for distributed tracing even if span id is invalid.
    """
    test_traceparent = (
        "00-a4f7651916cd43dd8448eb211c80319c-0000000000000000-01"
    )

    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_traceparent=test_traceparent,
    )
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    expected_trace_id = test_traceparent.split("-")[1]
    for span in spans:
        span_trace_id = format(span.context.trace_id, "x")
        assert span_trace_id == expected_trace_id


def test_otel_traceparent_without_tracing_enabled(test_exporter):
    """
    Tests that otel_traceparent is ignored when tracing is disabled.
    """
    test_traceparent = (
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    )

    mockplan = TestplanMock(name="MockPlan", otel_traceparent=test_traceparent)
    assert tracing._tracing_enabled is False

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 0


def test_conditional_span_with_true_condition(test_exporter):
    """
    Tests that conditional_span creates a span when condition is True.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[ConditionalSpanSuite()])
    )
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    conditional_span = find_span(spans, "conditional_op")
    assert conditional_span is not None
    assert conditional_span.attributes.get("op_type") == "test"


def test_conditional_span_with_false_condition(test_exporter):
    """
    Tests that conditional_span does not create a span when condition is False.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(
        MultiTest(name="MyMultitest", suites=[ConditionalSpanSuite()])
    )
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    skipped_span = find_span(spans, "skipped_op")
    assert skipped_span is None, (
        "No span should be created when condition is False"
    )


def test_trace_decorator(test_exporter):
    """
    Tests that the trace decorator creates spans for decorated methods.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[DecoratorSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()

    decorated_span = find_span(spans, "_decorated_operation")
    test_case_span = find_span(spans, "test_decorated_method")

    assert decorated_span is not None
    assert test_case_span is not None
    assert decorated_span.parent.span_id == test_case_span.context.span_id
    assert decorated_span.attributes.get("level") == "DecoratorSpanSuite"


def test_inject_root_context_prints_trace_id(test_exporter, capsys):
    """
    Tests that _inject_root_context prints the trace ID.
    """
    test_traceparent = (
        "00-a4f7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    )

    mockplan = TestplanMock(
        name="MockPlan",
        otel_traces=TraceLevel.TESTCASE,
        otel_traceparent=test_traceparent,
    )
    assert tracing._tracing_enabled

    mockplan.add(MultiTest(name="MyMultitest", suites=[MySuite()]))
    mockplan.run()

    # Capture printed output
    captured = capsys.readouterr()
    expected_trace_id = test_traceparent.split("-")[1]
    assert f"Trace ID: {expected_trace_id}" in captured.out


def test_conditional_span_when_tracing_disabled(test_exporter):
    """
    Tests that conditional_span does nothing when tracing is disabled.
    """
    mockplan = TestplanMock(name="MockPlan")
    assert tracing._tracing_enabled is False

    with tracing.conditional_span("disabled_span", condition=True) as span:
        assert span is None

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 0


def test_trace_decorator_when_tracing_disabled(test_exporter):
    """
    Tests that trace decorator works normally when tracing is disabled.
    """
    mockplan = TestplanMock(name="MockPlan")
    assert tracing._tracing_enabled is False

    mockplan.add(MultiTest(name="MyMultitest", suites=[DecoratorSpanSuite()]))
    mockplan.run()

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 0


def test_set_span_attrs_with_none_span(test_exporter):
    """
    Tests that set_span_attrs handles None span gracefully.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    # Should not raise an error
    tracing.set_span_attrs(span=None, attr1="value1")


def test_set_span_as_failed_with_none_span(test_exporter):
    """
    Tests that set_span_as_failed handles None span gracefully.
    """
    mockplan = TestplanMock(name="MockPlan", otel_traces=TraceLevel.TESTCASE)
    assert tracing._tracing_enabled

    # Should not raise an error
    tracing.set_span_as_failed(span=None, description="Test failure")
