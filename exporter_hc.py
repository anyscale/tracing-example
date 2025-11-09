from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from typing import List
from opentelemetry.sdk.trace import SpanProcessor


def honeycomb_span_processors() -> List[SpanProcessor]:
    # Reads OTEL_* env vars; no arguments needed
    return [BatchSpanProcessor(OTLPSpanExporter())]

