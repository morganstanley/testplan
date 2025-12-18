"""
OpenTelemetry observability integration for Testplan.

This module provides tracing capabilities using OpenTelemetry to monitor
and analyze test execution across distributed systems.
"""

from contextlib import contextmanager
import os
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional
from functools import wraps

from testplan.common.utils.logger import Loggable

if TYPE_CHECKING:
    from opentelemetry.context.context import Context
    from opentelemetry.sdk.trace import Span


class RootTraceIdGenerator:
    """
    Custom ID generator that uses a root trace ID when available.
    Falls back to random ID generation when no root trace ID is set.
    """

    def __init__(self, tracing_instance: "Tracing") -> None:
        """
        Initialize the ID generator.

        :param tracing_instance: Reference to the Tracing instance
        :type tracing_instance: Tracing
        """
        from opentelemetry.sdk.trace import RandomIdGenerator  # pylint: disable=import-error

        self._random_generator = RandomIdGenerator()
        self._tracing_instance = tracing_instance

    def generate_trace_id(self) -> int:
        """
        Generate a trace ID, using the root trace ID if available.

        :return: Trace ID as integer
        :rtype: int
        """
        traceparent = self._tracing_instance._get_traceparent()
        if traceparent:
            # Format: 00-{trace_id}-{span_id}-{flags}
            trace_id_hex = traceparent.split("-")[1]
            return int(trace_id_hex, 16)
        return self._random_generator.generate_trace_id()

    def generate_span_id(self) -> int:
        """
        Generate a span ID using random generation.

        :return: Span ID as integer
        :rtype: int
        """
        return self._random_generator.generate_span_id()


class Tracing(Loggable):
    """
    Global tracing object to handle OpenTelemetry tracing.

    This class manages the lifecycle of OpenTelemetry spans for Testplan execution,
    providing both automatic and manual span creation capabilities.

    The class is instantiated as a singleton (:py:data:`tracing`) and should be accessed
    through that global instance. Tracing is automatically enabled when OTEL environment
    variables are detected.

    Required Environment Variables:
        - ``OTEL_EXPORTER_OTLP_TRACES_ENDPOINT``: OTLP traces endpoint URL
        - ``OTEL_EXPORTER_OTLP_HEADERS``: OTLP headers
        - ``OTEL_EXPORTER_OTLP_CERTIFICATE``: Path to CA certificate
        - ``OTEL_EXPORTER_OTLP_CLIENT_KEY``: Path to client private key
        - ``OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE``: Path to client certificate
        - ``OTEL_RESOURCE_ATTRIBUTES``: Resource attributes as comma-separated key=value pairs

    Optional Environment Variables:
        - ``OTEL_BSP_SCHEDULE_DELAY``: Batch span processor delay in milliseconds (default: 200)
    """

    def __init__(self):
        super().__init__()
        self._tracing_enabled = False
        self._root_context = {}
        self._tracer = None
        self._tracer_provider = None
        self._root_span = None

    def __str__(self):
        return "Tracing"

    def _setup(self, traceparent: Optional[str] = None) -> None:
        """
        Called internally to initialize OpenTelemetry tracing based on environment variables.

        Tracing is enabled when any environment variable starting with ``OTEL_``
        is detected. Required TLS certificates must be provided for gRPC exporter.

        :param root_trace: Optional root trace context in W3C traceparent format
        :type traceparent: Optional[str]
        """
        if traceparent:
            self._root_context = {"traceparent": traceparent}

        try:
            import grpc
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
        except ImportError as e:
            raise RuntimeError(
                "Certain packages failed to import, please consider install Testplan "
                "package with `observability` extra to enable tracing."
            ) from e

        required = [
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "OTEL_EXPORTER_OTLP_HEADERS",
            "OTEL_EXPORTER_OTLP_CERTIFICATE",
            "OTEL_EXPORTER_OTLP_CLIENT_KEY",
            "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE",
            "OTEL_RESOURCE_ATTRIBUTES",
        ]
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                f"Missing required OTEL environment variables: {', '.join(missing)}"
            )

        root_cert = os.environ["OTEL_EXPORTER_OTLP_CERTIFICATE"]
        private_key = os.environ["OTEL_EXPORTER_OTLP_CLIENT_KEY"]
        certificate_chain = os.environ["OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE"]
        with (
            open(root_cert, "rb") as rc,
            open(private_key, "rb") as pk,
            open(certificate_chain, "rb") as cc,
        ):
            credentials = grpc.ssl_channel_credentials(
                root_certificates=rc.read(),
                private_key=pk.read(),
                certificate_chain=cc.read(),
            )

        provider = TracerProvider(id_generator=RootTraceIdGenerator(self))
        # Tune BatchSpanProcessor for short-lived worker processes:
        # Allow overriding via environment, else use more aggressive default.
        schedule_delay = int(os.getenv("OTEL_BSP_SCHEDULE_DELAY", 200))
        processor = BatchSpanProcessor(
            OTLPSpanExporter(credentials=credentials),
            schedule_delay_millis=schedule_delay,
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer("testplan_tracer")
        self._tracer_provider = provider
        self._tracing_enabled = True

    @contextmanager
    def span(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Iterator[Optional["Span"]]:
        """
        Create a span using context manager (recommended approach).

        :param name: Name of the span
        :type name: str
        :param context: Optional trace context for span propagation, defaults to current parent span if not provided
        :type context: Optional[Dict[str, Any]]
        :param kwargs: Additional span attributes as keyword arguments
        :type kwargs: Any

        :yield: Span object if tracing is enabled, None otherwise
        :rtype: Iterator[Optional[Span]]

        Example:
            >>> with tracing.span("operation", example_attr="value1") as span:
            ...     # Perform operation
            ...     pass
        """
        if not self._tracing_enabled:
            yield
            return
        with self._tracer.start_as_current_span(
            name, context=context, attributes=kwargs
        ) as span:
            yield span

    @contextmanager
    def conditional_span(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
        condition: bool = True,
        **kwargs,
    ) -> Iterator[Optional["Span"]]:
        """
        Utility function to create a span conditionally.

        :param name: Name of the span
        :type name: str
        :param context: Optional trace context for span propagation, defaults to current parent span if not provided
        :type context: Optional[Dict[str, Any]]
        :param condition: Condition to determine whether to create the span
        :type condition: bool
        :param kwargs: Additional span attributes as keyword arguments
        :type kwargs: Any

        :yield: Span object if tracing is enabled and condition is met, None otherwise
        :rtype: Iterator[Optional[Span]]

        Example:
            >>> with tracing.conditional_span("operation", condition=True, example_attr="value1") as span:
            ...     # Perform operation
            ...     pass
        """
        if not self._tracing_enabled or not condition:
            yield
            return
        with self.span(name, context=context, **kwargs) as span:
            yield span

    def start_span(
        self,
        span_name: str,
        context: Optional[Dict[str, Any]] = None,
        start_time: Optional[int] = None,
        **kwargs,
    ) -> Optional["Span"]:
        """
        Manually start a span (use when context manager is not suitable).

        The span must be explicitly ended using :py:meth:`end_span` else it will not be exported.

        :param span_name: Name of the span
        :type span_name: str
        :param context: Optional trace context for span propagation
        :type context: Optional[Dict[str, Any]]
        :param start_time: Optional start time in nanoseconds since epoch
        :type start_time: Optional[int]
        :param kwargs: Additional span attributes as keyword arguments
        :type kwargs: Any

        :return: Span object if tracing is enabled, None otherwise
        :rtype: Optional[Span]

        Example:
            >>> span = tracing.start_span("operation", task_id="123")
            >>> try:
            ...     # Perform operation
            ...     pass
            ... finally:
            ...     tracing.end_span("operation")
        """
        if not self._tracing_enabled:
            return None
        return self._tracer.start_span(
            span_name,
            context=context,
            start_time=start_time,
            attributes=kwargs,
        )

    def end_span(self, span: "Span", end_time: Optional[int] = None) -> None:
        """
        Manually end a span started with :py:meth:`start_span`.

        :param span: Span to end
        :type span: Span
        :param end_time: Optional end time in nanoseconds since epoch
        :type end_time: Optional[int]

        Example:
            >>> tracing.start_span("operation")
            >>> # Perform operation
            >>> tracing.end_span("operation")
        """
        if not self._tracing_enabled:
            return
        span.end(end_time=end_time)

    def _inject_root_context(self, span: "Span") -> None:
        """
        Inject root trace context for distributed tracing.

        This is called internally to propagate trace context to child
        threads.
        """
        if not self._tracing_enabled:
            return
        from opentelemetry.propagate import inject  # pylint: disable=import-error

        inject(self._root_context)
        self._root_span = span
        if trace := self._get_traceparent():
            # root trace is in the format of 00-d1b9e555b056907ee20b0daebf62282c-7dcd821387246e1c-01
            # 00 is a version number which you can ignore.
            # d1b9e555b056907ee20b0daebf62282c is the trace_id.
            # 7dcd821387246e1c is the span_id of the parent span, i.e. the parent_span_id of the child log.
            # 01 is the trace_flags field and indicates that the trace should be included by sampling.
            self.logger.user_info(f"Trace ID: {trace.split('-')[1]}")

    def _get_root_context(self) -> "Context":
        """
        Extract root trace context for distributed tracing.

        :return: Extracted trace context
        :rtype: Dict[str, object]
        """
        if not self._tracing_enabled:
            return {}
        from opentelemetry.propagate import extract  # pylint: disable=import-error

        return extract(self._root_context)

    def _get_traceparent(self) -> str:
        """
        Get the traceparent.

        :return: Traceparent string or empty string if not set
        :rtype: str
        """
        return self._root_context.get("traceparent", "")

    def _get_root_span(self) -> Optional["Span"]:
        """
        Get the root span.

        :return: Root span or None if tracing not enabled
        :rtype: Optional[Span]
        """
        if not self._tracing_enabled:
            return None

        return self._root_span

    def set_span_as_failed(
        self, span: Optional["Span"] = None, description: Optional[str] = None
    ) -> None:
        """
        Mark a span as failed with an error status.

        :param span: Span to mark as failed, if None, do nothing
        :type span: Optional[Span]
        :param description: Optional error description
        :type description: Optional[str]

        Example:
            >>> with tracing.span("validation") as span:
            ...     if not is_valid:
            ...         tracing.set_span_as_failed(
            ...             span,
            ...             description="Validation failed"
            ...         )
        """
        if not self._tracing_enabled or span is None:
            return None
        from opentelemetry import trace  # pylint: disable=import-error

        span.set_status(
            trace.StatusCode.ERROR,
            description,
        )

    def set_span_attrs(self, span: Optional["Span"] = None, **kwargs) -> None:
        """
        Set attributes on a span.

        :param span: Span to set attributes on, if None, do nothing
        :type span: Optional[Span]
        :param kwargs: Attributes as keyword arguments
        :type kwargs: Any

        Example:
            >>> with tracing.span("api_call") as span:
            ...     response = call_api()
            ...     tracing.set_span_attrs(
            ...         span,
            ...         status_code=response.status_code,
            ...         response_time_ms=response.elapsed
            ...     )
        """
        if not self._tracing_enabled or span is None:
            return None
        span.set_attributes(kwargs)

    def force_flush(self) -> None:
        """
        Force the current span processor to export all ended spans.
        """
        if self._tracer_provider:
            self._tracer_provider.force_flush()

    def trace(self, func):
        """
        A decorator that wraps a function with a span.

        Example:
            >>> @tracing.trace
            ... def my_function():
            ...     # Function implementation
            ...     pass
        """

        @wraps(func)
        def _wrapped(instance_self, *args, **kwargs):
            with self.span(
                name=func.__name__, level=instance_self.__class__.__name__
            ):
                return func(instance_self, *args, **kwargs)

        return _wrapped


#: Global tracing instance for Testplan observability
tracing = Tracing()
