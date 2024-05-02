
import os 

from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.ext.honeycomb import HoneycombSpanExporter

from typing import List

def default_tracing_exporter() -> List[SimpleSpanProcessor]:
    exporter = HoneycombSpanExporter(
        service_name="test-service",
        writekey="",
        dataset="",
    )

    return [BatchSpanProcessor(exporter)]