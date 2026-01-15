import logging
import os

from testplan.common.utils.logger import Loggable, TESTPLAN_LOGGER


class OtelLogging(Loggable):
    """
    Global logging object to handle OpenTelemetry logging integration.

    This class manages the lifecycle of OpenTelemetry logging for Testplan execution,
    enabling log collection and correlation with distributed traces. It attaches to the
    Testplan logger and exports logs to Grafana Loki.

    The class is instantiated as a singleton (:py:data:`otel_logging`) and should be accessed
    through that global instance.

    .. note::
        This class must be run alongside the tracing setup (:py:data:`tracing`) to ensure
        logs are properly correlated with traces via trace_id and span_id.

    Required Environment Variables:
        - ``OTEL_EXPORTER_LOKI_ENDPOINT``: Loki endpoint URL
        - ``OTEL_EXPORTER_OTLP_HEADERS``: OTLP headers
        - ``OTEL_EXPORTER_OTLP_CERTIFICATE``: Path to CA certificate
        - ``OTEL_EXPORTER_OTLP_CLIENT_KEY``: Path to client private key
        - ``OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE``: Path to client certificate
    """

    def __init__(self):
        super().__init__()
        self._logging_enabled = False
        self._logger_provider = None

    def _setup(self):
        """
        Called internally to setup OpenTelemetry logging infrastructure.

        Initializes the OTEL LoggerProvider, creates a Loki exporter, and attaches
        a logging handler to the Testplan logger. All subsequent logs to
        TESTPLAN_LOGGER will be captured and exported to Loki.
        """
        try:
            from opentelemetry import _logs
            from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            from testplan.common.utils.observability.loki_exporter import (
                LokiExporter,
            )
        except ImportError as e:
            raise RuntimeError(
                "Certain packages failed to import, please consider install Testplan "
                "package with `observability` extra to enable logging."
            ) from e

        required = [
            "OTEL_EXPORTER_OTLP_CERTIFICATE",
            "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE",
            "OTEL_EXPORTER_OTLP_CLIENT_KEY",
            "OTEL_EXPORTER_OTLP_HEADERS",
            "OTEL_EXPORTER_LOKI_ENDPOINT",
        ]
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                f"Missing required OTEL environment variables: {', '.join(missing)}"
            )

        self._logging_enabled = True
        self._logger_provider = LoggerProvider()
        _logs.set_logger_provider(self._logger_provider)
        # We need a custom exporter since the internal otel collector setup does not support logs export yet
        # This can be replaced with OTLPLogExporter once the setup supports it
        exporter = LokiExporter(
            ca_cert=os.environ.get("OTEL_EXPORTER_OTLP_CERTIFICATE"),
            client_cert=os.environ.get(
                "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE"
            ),
            client_key=os.environ.get("OTEL_EXPORTER_OTLP_CLIENT_KEY"),
            header=os.environ.get("OTEL_EXPORTER_OTLP_HEADERS"),
            endpoint=os.environ.get("OTEL_EXPORTER_LOKI_ENDPOINT"),
        )
        self._logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(exporter)
        )

        logging_handler = LoggingHandler(logger_provider=self._logger_provider)
        logging_handler.setLevel(logging.DEBUG)
        TESTPLAN_LOGGER.addHandler(logging_handler)

    def force_flush(self):
        """
        Force the current log processor to export all recorded logs.
        """
        if self._logger_provider:
            self._logger_provider.force_flush()


otel_logging = OtelLogging()
