import pytest
from unittest.mock import MagicMock

from opentelemetry.sdk.trace import _Span
from opentelemetry.trace import (
    SpanContext,
    StatusCode,
    TraceFlags,
    NonRecordingSpan,
    TraceState,
    set_span_in_context,
)


def test_tracing_disabled_by_default(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    assert tracing._tracing_enabled is False
    with tracing.span("no_op_span") as span:
        assert span is None
    assert tracing.start_span("no_op_span") is None
    mock_span = MagicMock(spec=_Span)
    tracing.end_span(mock_span)
    mock_span.end.assert_not_called()
    tracing.set_span_as_failed()
    tracing.set_span_attrs(attr="value")
    assert len(exporter.get_finished_spans()) == 0


def test_span_context_manager(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    with tracing.span("my_span", attr1="value1", attr2=123):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "my_span"
    assert span.attributes == {"attr1": "value1", "attr2": 123}
    assert span.status.is_ok


def test_manual_start_end_span(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    span = tracing.start_span("manual_span", attr2="value2")
    assert span is not None
    assert isinstance(span, _Span)
    tracing.end_span(span)
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    finished = spans[0]
    assert finished.name == "manual_span"
    assert finished.attributes == {"attr2": "value2"}
    assert finished.status.is_ok


def test_set_span_as_failed(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    with tracing.span("failing_span") as span:
        tracing.set_span_as_failed(span, "It broke")
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "failing_span"
    assert span.status.status_code == StatusCode.ERROR
    assert span.status.description == "It broke"


def test_set_span_as_failed_with_none_span(unit_test_tracing):
    """Test that set_span_as_failed handles None span gracefully."""
    tracing, exporter = unit_test_tracing
    tracing._setup()
    # Should not raise an error
    tracing.set_span_as_failed(span=None, description="Test failure")
    assert len(exporter.get_finished_spans()) == 0


def test_set_span_attributes(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    with tracing.span("attribute_span") as span:
        tracing.set_span_attrs(span, attr3="value3", attr4=456)
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "attribute_span"
    assert span.attributes == {"attr3": "value3", "attr4": 456}


def test_set_span_attrs_with_none_span(unit_test_tracing):
    """Test that set_span_attrs handles None span gracefully."""
    tracing, exporter = unit_test_tracing
    tracing._setup()
    # Should not raise an error
    tracing.set_span_attrs(span=None, attr1="value1")
    assert len(exporter.get_finished_spans()) == 0


def test_conditional_span_with_true_condition(unit_test_tracing):
    """Test conditional_span creates a span when condition is True."""
    tracing, exporter = unit_test_tracing
    tracing._setup()
    with tracing.conditional_span(
        "conditional_span", condition=True, op_type="test"
    ) as span:
        assert span is not None
        assert isinstance(span, _Span)
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "conditional_span"
    assert span.attributes == {"op_type": "test"}


def test_conditional_span_with_false_condition(unit_test_tracing):
    """Test conditional_span does not create a span when condition is False."""
    tracing, exporter = unit_test_tracing
    tracing._setup()
    with tracing.conditional_span(
        "skipped_span", condition=False, op_type="test"
    ) as span:
        assert span is None
    spans = exporter.get_finished_spans()
    assert len(spans) == 0


def test_conditional_span_when_tracing_disabled(unit_test_tracing):
    """Test conditional_span does nothing when tracing is disabled."""
    tracing, exporter = unit_test_tracing
    with tracing.conditional_span("disabled_span", condition=True) as span:
        assert span is None
    spans = exporter.get_finished_spans()
    assert len(spans) == 0


def test_trace_decorator(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()

    class MyClass:
        @tracing.trace
        def my_method(self, arg1, kwarg1=None):
            return f"Result: {arg1}, {kwarg1}"

    result = MyClass().my_method("foo", kwarg1="bar")
    assert result == "Result: foo, bar"
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "my_method"
    assert spans[0].attributes == {"level": "MyClass"}


def test_trace_decorator_when_tracing_disabled(unit_test_tracing):
    """Test trace decorator works normally when tracing is disabled."""
    tracing, exporter = unit_test_tracing

    class MyClass:
        @tracing.trace
        def my_method(self, arg1, kwarg1=None):
            return f"Result: {arg1}, {kwarg1}"

    result = MyClass().my_method("foo", kwarg1="bar")
    assert result == "Result: foo, bar"
    spans = exporter.get_finished_spans()
    assert len(spans) == 0


def test_parent_trace_propagation(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    _v, trace_id_hex, span_id_hex, flags_hex = traceparent.split("-")
    parent_ctx = SpanContext(
        trace_id=int(trace_id_hex, 16),
        span_id=int(span_id_hex, 16),
        is_remote=True,
        trace_flags=TraceFlags(int(flags_hex, 16)),
        trace_state=TraceState(),
    )
    ctx = set_span_in_context(NonRecordingSpan(parent_ctx))
    child_span = tracing.start_span("child_span", context=ctx)
    assert child_span is not None
    child_span.end()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    finished = spans[0]
    assert finished.context.trace_id == int(trace_id_hex, 16)
    assert finished.parent.span_id == int(span_id_hex, 16)


def test_inject_root_context_disabled(unit_test_tracing, capsys):
    tracing, exporter = unit_test_tracing
    tracing._inject_root_context()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_inject_root_context_enabled(monkeypatch, unit_test_tracing, capsys):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    called = {}

    def fake_inject(carrier):
        called["carrier"] = carrier.copy()

    monkeypatch.setattr("opentelemetry.propagate.inject", fake_inject)
    traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    tracing._root_context = {"traceparent": traceparent}
    tracing._inject_root_context()
    captured = capsys.readouterr()
    assert "0af7651916cd43dd8448eb211c80319c" in captured.out
    assert called["carrier"]["traceparent"] == traceparent


def test_get_traceparent_values(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._root_context = {"traceparent": "00-abc-123-01"}
    assert tracing._get_traceparent() == "00-abc-123-01"


def test_get_root_context_disabled(unit_test_tracing):
    tracing, exporter = unit_test_tracing
    assert tracing._get_root_context() == {}


def test_get_root_context_enabled(monkeypatch, unit_test_tracing):
    tracing, exporter = unit_test_tracing
    tracing._setup()
    fake_extracted = {"trace_id": "deadbeef"}

    def fake_extract(carrier):
        assert carrier == {
            "traceparent": "00-deadbeefcafebabe-ffee112233445566-01"
        }
        return fake_extracted

    monkeypatch.setattr("opentelemetry.propagate.extract", fake_extract)
    tracing._root_context = {
        "traceparent": "00-deadbeefcafebabe-ffee112233445566-01"
    }
    assert tracing._get_root_context() == fake_extracted
