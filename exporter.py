from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.ext.honeycomb import HoneycombSpanExporter

from typing import List

def default_tracing_exporter() -> List[SpanProcessor]:
    exporter = HoneycombSpanExporter(
        service_name="",
        writekey="",
        dataset="",
    )

    return [BatchSpanProcessor(exporter)]