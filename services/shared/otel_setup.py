"""
Shared OpenTelemetry instrumentation setup.

Represents the "centralised observability configuration" from
the product service's perspective. The platform team distributes
this helper so product engineers get standardised instrumentation
out of the box.

Usage:
    from otel_setup import setup_otel, get_tracer, get_meter, get_logger
    setup_otel(service_name="my-service")
    tracer = get_tracer("my-service")
"""

import logging
import os

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource


def setup_otel(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    collector_endpoint: str | None = None,
):
    """
    Initialise all three pillars of OpenTelemetry: traces, metrics, logs.

    Parameters
    ----------
    service_name : str
        Identifies this service in dashboards and traces.
    service_version : str
        Semantic version. Useful for tracking regressions after deploys.
    environment : str
        Deployment environment (development, staging, production).
    collector_endpoint : str or None
        OTel Collector gRPC endpoint. Defaults to OTEL_EXPORTER_OTLP_ENDPOINT
        env var, then http://otel-collector:4317.
    """
    endpoint = collector_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
    )

    # Resource: describes the entity producing telemetry
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": environment,
    })

    # TRACES
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(trace_provider)

    # METRICS
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=15_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # LOGS
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    set_logger_provider(logger_provider)
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)