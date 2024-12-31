from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace import SpanProcessor
from typing import List


def debug_span_processor() -> List[SpanProcessor]:
    return [SimpleSpanProcessor(ConsoleSpanExporter())]
