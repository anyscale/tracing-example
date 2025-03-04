import ray

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import Span, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _add_ray_serve_context(span: Span) -> None:
    """Add Ray Serve context metadata into Datadog span."""
    # add Ray Serve context
    ray_context = ray.get_runtime_context()
    span.set_attribute("ray.job_id", ray_context.get_job_id())
    span.set_attribute("ray.actor_id", ray_context.get_actor_id())
    span.set_attribute("ray.task_id", ray_context.get_task_id())

    # add request id
    serve_request_context = ray.serve.context._get_serve_request_context()
    span.set_attribute("ray.request_id", serve_request_context.request_id)


class RayServeSpanProcessor(SpanProcessor):
    """Custom OTEL SpanProcessor that injects Ray context."""
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        """Start span event hook.

        Inject Ray Serve context information.
        """
        _add_ray_serve_context(span)
        return super().on_start(span, parent_context)


def datadog_span_processor() -> SpanProcessor:
    """Return OTEL OTLP SpanExporter for integration with Datadog.

    To enable span export to Datadog over HTTP,
        1. ensure the following deps are installed:

            opentelemetry-exporter-otlp
            opentelemetry-exporter-otlp-proto-http

        2. set the envvar:

            OTEL_EXPORTER_OTLP_ENDPOINT=http://[datadog host]:4318
    """
    return BatchSpanProcessor(OTLPSpanExporter())


def anyscale_span_processors() -> list[SpanProcessor]:
    """Add span processors to instrumentation for use by Anyscale.

    Automagically, Anyscale adds SpanProcessors to the default TracerProvider during
    tracing initialization. In particular, the value of the envvar

        ANYSCALE_TRACING_EXPORTER_IMPORT_PATH=exporter_dd:anyscale_span_processors

    should be an importable function which returns a list of SpanProcessors.
    """
    return [
        RayServeSpanProcessor(),
        datadog_span_processor(),
    ]
