"""OpenTelemetry tracing — per-item pipeline spans (Member D — D1)."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

from observability.redaction import safe_span_attribute

_tracer = None
_memory_exporter = None
_configured = False


def setup_tracing(*, force_memory: bool = False) -> None:
    """Configure OTel tracer provider. Uses in-memory export when no collector is set."""
    global _tracer, _memory_exporter, _configured
    if _configured:
        return

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    resource = Resource.create({"service.name": "nightshift"})
    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_ENDPOINT", "").strip()
    use_memory = force_memory or os.getenv("OTEL_USE_MEMORY", "").lower() in {"1", "true", "yes"}

    if use_memory or not endpoint:
        _memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_memory_exporter))
    else:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception:
            _memory_exporter = InMemorySpanExporter()
            provider.add_span_processor(SimpleSpanProcessor(_memory_exporter))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("nightshift")
    _configured = True


def reset_tracing_for_tests() -> None:
    """Test helper — clear finished spans without replacing the global provider."""
    clear_finished_spans()


def get_tracer():
    if not _configured:
        setup_tracing()
    return _tracer


def clear_finished_spans() -> None:
    if _memory_exporter is not None:
        _memory_exporter.clear()


def finished_spans():
    if _memory_exporter is None:
        return []
    return _memory_exporter.get_finished_spans()


def set_attributes(**attrs: Any) -> None:
    from opentelemetry import trace

    span = trace.get_current_span()
    if not span.is_recording():
        return
    for key, value in attrs.items():
        safe_key, safe_value = safe_span_attribute(key, value)
        span.set_attribute(safe_key, safe_value)


@contextmanager
def item_span(raw_item_id: str, source: str) -> Iterator[None]:
    """Top-level span for one overnight item (ingest → triage → draft)."""
    tracer = get_tracer()
    with tracer.start_as_current_span("nightshift.process_item") as span:
        set_attributes(item_id=raw_item_id, item_source=source)
        yield


@contextmanager
def agent_span(
    agent: str,
    *,
    model: str | None = None,
    backend: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Child span for triage/response with optional model metadata."""
    tracer = get_tracer()
    meta: dict[str, Any] = {}
    start = time.perf_counter()
    with tracer.start_as_current_span(f"nightshift.{agent}") as span:
        attrs: dict[str, Any] = {"agent.name": agent}
        if model:
            attrs["gen_ai.request.model"] = model
        if backend:
            attrs["agent.backend"] = backend
        set_attributes(**attrs)
        try:
            yield meta
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            span.set_attribute("agent.latency_ms", elapsed_ms)
            if "input_tokens" in meta:
                span.set_attribute("gen_ai.usage.input_tokens", meta["input_tokens"])
            if "output_tokens" in meta:
                span.set_attribute("gen_ai.usage.output_tokens", meta["output_tokens"])


@contextmanager
def tool_span(tool_name: str) -> Iterator[None]:
    """Span for MCP or sandbox tool calls."""
    tracer = get_tracer()
    start = time.perf_counter()
    with tracer.start_as_current_span(f"nightshift.tool.{tool_name}") as span:
        span.set_attribute("tool.name", tool_name)
        yield
        span.set_attribute("tool.latency_ms", round((time.perf_counter() - start) * 1000, 2))
