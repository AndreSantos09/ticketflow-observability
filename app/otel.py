"""OpenTelemetry setup: traces, metrics and logs exported via OTLP/gRPC.

This is intentionally simple. It wires up:
  - Traces  -> OTLP/gRPC -> Collector -> Tempo
  - Metrics -> OTLP/gRPC -> Collector -> Prometheus
  - Logs    -> OTLP/gRPC -> Collector -> Loki

Auto-instrumentation for FastAPI and psycopg gives HTTP + DB spans/metrics
out of the box, so the demo stays small.
"""
import logging

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import config


def setup_telemetry() -> None:
    resource = Resource.create(
        {
            "service.name": config.OTEL_SERVICE_NAME,
            "service.namespace": "ticketflow",
        }
    )

    endpoint = config.OTEL_EXPORTER_OTLP_ENDPOINT

    # ---- Traces ----
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # ---- Metrics ----
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=5000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # ---- Logs ----
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(otel_handler)
    # Also log to stdout so `docker compose logs` shows something useful.
    root_logger.addHandler(logging.StreamHandler())

    logging.getLogger(__name__).info(
        "OpenTelemetry initialised (endpoint=%s, service=%s)",
        endpoint,
        config.OTEL_SERVICE_NAME,
    )
