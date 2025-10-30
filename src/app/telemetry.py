"""Basic OpenTelemetry setup for observability."""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_telemetry(app_name: str = "py-ai"):
    """Initialize OpenTelemetry tracing and metrics."""

    # Only setup if OTEL endpoint is configured
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping telemetry setup")
        return

    # Resource identifies this service
    resource = Resource.create(
        {
            "service.name": app_name,
            "service.version": "0.1.0",
        }
    )

    # Setup tracing
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)

    # OTLP span exporter
    span_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
    span_processor = BatchSpanProcessor(span_exporter)
    trace_provider.add_span_processor(span_processor)

    # Setup metrics
    metric_exporter = OTLPMetricExporter(endpoint=otel_endpoint)
    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=30000,  # 30 seconds
    )
    metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metrics_provider)

    logger.info(f"OpenTelemetry configured with endpoint: {otel_endpoint}")


def instrument_app(app):
    """Instrument FastAPI app and HTTP clients."""

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Auto-instrument httpx (used by AI providers)
    HTTPXClientInstrumentor().instrument()

    logger.info("FastAPI and httpx instrumentation enabled")


def get_tracer(name: str):
    """Get a tracer for manual instrumentation."""
    return trace.get_tracer(name)


def get_meter(name: str):
    """Get a meter for custom metrics."""
    return metrics.get_meter(name)


# Custom metrics for AI operations
def create_ai_metrics():
    """Create custom metrics for AI service operations."""
    meter = get_meter("py-ai.ai-service")

    # Counter for AI requests
    ai_requests_counter = meter.create_counter(
        name="ai_requests_total", description="Total number of AI requests", unit="1"
    )

    # Histogram for AI request duration
    ai_request_duration = meter.create_histogram(
        name="ai_request_duration_ms", description="AI request duration in milliseconds", unit="ms"
    )

    # Counter for tokens
    ai_tokens_counter = meter.create_counter(
        name="ai_tokens_total", description="Total AI tokens consumed", unit="1"
    )

    return {
        "requests": ai_requests_counter,
        "duration": ai_request_duration,
        "tokens": ai_tokens_counter,
    }
