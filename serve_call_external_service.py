import asyncio
import requests
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.trace.status import Status, StatusCode
from ray import serve
from ray.anyscale.serve._private.tracing_utils import (
    get_trace_context,
)
from starlette.requests import Request


@serve.deployment
class UpstreamApp:
    def __call__(self, request: Request):
        # Create a new span that is associated with the current trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "upstream_application_span", context=get_trace_context()
        ) as span:
            url = f"{str(request.url).replace('http://', 'https://')}downstream"
            headers = {"Authorization": request.headers.get("authorization")}

            # Inject the trace context into the headers to propagate it downstream.
            ctx = get_trace_context()
            TraceContextTextMapPropagator().inject(headers, ctx)

            # Go out to network to call the downstream service.
            resp = requests.get(url, headers=headers)

            replica_context = serve.get_replica_context()
            # Update the span attributes and status
            attributes = {
                "deployment": replica_context.deployment,
                "replica_id": replica_context.replica_id.unique_id
            }
            span.set_attributes(attributes)
            span.set_status(
                Status(status_code=StatusCode.OK)
            )

            # Return message
            return {
                "upstream_message": "Hello world from UpstreamApp!",
                "downstream_message": resp.text,
            }


@serve.deployment
class DownstreamApp:
    async def __call__(self):
        # Create a new span that is associated with the current trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "downstream_application_span", context=get_trace_context()
        ) as span:
            replica_context = serve.get_replica_context()
            # Update the span attributes and status
            attributes = {
                "deployment": replica_context.deployment,
                "replica_id": replica_context.replica_id.unique_id
            }
            span.set_attributes(attributes)
            span.set_status(
                Status(status_code=StatusCode.OK)
            )

            # Simulate some work.
            await asyncio.sleep(0.5)

            # Return message
            return "Hello world from DownstreamApp!"


upstream_app = UpstreamApp.bind()
downstream_app = DownstreamApp.bind()
