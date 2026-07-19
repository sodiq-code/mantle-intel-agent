"""
Mantle Intel Agent — OpenTelemetry Tracing (P2-16)

Initialises a tracer provider with OTLP exporter (configurable via
OTEL_EXPORTER_OTLP_ENDPOINT).  If the endpoint is not set, falls back
to ConsoleSpanExporter (dev-friendly, zero infra needed).

Usage:
    from agents.tracing import tracer

    with tracer.start_as_current_span("pipeline.run_cycle") as span:
        span.set_attribute("cycle_number", 42)
        ...
"""
from __future__ import annotations

import os
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

_tracer: Optional[object] = None


def init_tracing(service_name: str = "mantle-intel-agent") -> Optional[object]:
    """Initialise OpenTelemetry tracing.

    Returns the tracer, or None if OTel is not installed.
    """
    global _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        logger.info("otel_not_installed",
                    msg="opentelemetry packages not installed. "
                        "Install with: pip install opentelemetry-api "
                        "opentelemetry-sdk opentelemetry-exporter-otlp")
        return None

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "2.0.0",
    })

    provider = TracerProvider(resource=resource)

    # Configure exporter based on environment
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("otel_otlp_exporter_configured", endpoint=otlp_endpoint)
        except ImportError:
            logger.warning("otel_otlp_not_installed",
                           msg="opentelemetry-exporter-otlp not installed. "
                               "Falling back to ConsoleSpanExporter. "
                               "Install with: pip install "
                               "opentelemetry-exporter-otlp")
            _add_console_exporter(provider)
    else:
        _add_console_exporter(provider)

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name, "2.0.0")
    logger.info("otel_tracing_initialized", service=service_name)
    return _tracer


def _add_console_exporter(provider) -> None:
    """Add ConsoleSpanExporter (dev-friendly, zero infra needed)."""
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(console_exporter))
    logger.info("otel_console_exporter_configured",
                msg="Spans will be printed to console. Set "
                    "OTEL_EXPORTER_OTLP_ENDPOINT for production.")


def get_tracer():
    """Get the global tracer, initialising if needed."""
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer


# Convenience: import and use directly
tracer = get_tracer()
