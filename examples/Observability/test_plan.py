#!/usr/bin/env python
"""
Example demonstrating OpenTelemetry observability in Testplan.
"""

import os
import sys
import time

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.observability import TraceLevel, tracing


# Configure OpenTelemetry environment variables
# In production, these would typically be set externally
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = (
    "https://otlp.example.com:4317"
)
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = "header1=value1"
os.environ["OTEL_EXPORTER_OTLP_CERTIFICATE"] = "/path/to/ca-cert.pem"
os.environ["OTEL_EXPORTER_OTLP_CLIENT_KEY"] = "/path/to/client-key.pem"
os.environ["OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE"] = (
    "/path/to/client-cert.pem"
)
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = (
    "service.name=testplan-example,environment=demo"
)


@testsuite
class TracingExamples:
    """Basic tracing examples."""

    @testcase
    def test_context_manager_span(self, env, result):
        """Using spans with context manager (recommended)."""
        with tracing.span("example_operation", operation_type="query") as span:
            time.sleep(0.1)
            result.log("Executing operation")
            result.true(True, description="Operation executed successfully")

    @testcase
    def test_start_end_span(self, env, result):
        """Using manual span start/end for explicit control."""
        span = tracing.start_span(
            "api_request", endpoint="/users", method="GET"
        )

        try:
            # Simulate API call
            time.sleep(0.05)
            response_code = 200

            result.equal(
                response_code, 200, description="API returned success"
            )
        finally:
            tracing.end_span(span)

    @testcase
    def test_nested_spans(self, env, result):
        """Creating nested spans for hierarchical operations."""
        with tracing.span("parent_operation", level="high") as parent_span:
            result.log("Starting parent operation")
            with tracing.span("child_operation_1", level="low") as child1:
                time.sleep(0.02)
                result.log("Child operation 1 complete")

    @testcase
    def test_setting_span_attributes(self, env, result):
        """Setting span attributes based on runtime data."""
        with tracing.span("data_processing") as span:
            # Simulate processing
            records_processed = 150
            errors_encountered = 2
            processing_time_ms = 234.5

            # Add attributes after processing
            tracing.set_span_attrs(
                span=span,
                records_processed=records_processed,
                errors_encountered=errors_encountered,
                processing_time_ms=processing_time_ms,
                success_rate=(records_processed - errors_encountered)
                / records_processed,
            )

    @testcase
    def test_setting_span_failure(self, env, result):
        """Marking spans as failed if required"""
        with tracing.span("failing_span") as span:
            is_valid = False
            if not is_valid:
                tracing.set_span_as_failed(
                    span=span, description="Validation failed"
                )
                result.fail("Validation failed")
            else:
                result.true(True, description="Validation passed")


@testsuite
class MultiTestCaseSpan:
    """Span spanning multiple test cases."""

    span = None

    @testcase
    def test_workflow_step_1(self, env, result):
        """
        Initialize workflow and start long-running span.
        The span will be nested under the testcase that started the span.
        """
        # Start a span that will continue across test cases
        self.span = tracing.start_span(
            "multi_step_workflow", workflow_id="wf-12345", total_steps=3
        )

    @testcase
    def test_workflow_step_2(self, env, result):
        """Complete workflow and end span."""
        # End the multi-step span
        tracing.end_span(self.span)


@test_plan(name="ObservabilityExample", otel_traces=TraceLevel.TEST)
def main(plan):
    """
    Testplan demonstrating observability features.
    """
    plan.add(
        MultiTest(
            name="TracingExamples",
            suites=[
                TracingExamples(),
                MultiTestCaseSpan(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(main().exit_code)
