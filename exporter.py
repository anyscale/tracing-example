import os

from opentelemetry.ext.honeycomb import HoneycombSpanExporter
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from typing import List

# Replace those with the actual values.
HONEYCOMB_SERVICE_NAME = os.getenv("HONEYCOMB_SERVICE_NAME", "")
HONEYCOMB_WRITE_KEY = os.getenv("HONEYCOMB_WRITE_KEY", "")
HONEYCOMB_DATASET_NAME = os.getenv("HONEYCOMB_DATASET_NAME", "")


def default_tracing_exporter() -> List[SpanProcessor]:
    exporter = HoneycombSpanExporter(
        service_name=HONEYCOMB_SERVICE_NAME,
        writekey=HONEYCOMB_WRITE_KEY,
        dataset=HONEYCOMB_DATASET_NAME,
    )
    return [BatchSpanProcessor(exporter)]
