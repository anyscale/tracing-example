from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from ray import serve
from typing import Optional, Dict

from fp import FastAPIInstrumentor


def get_serve_trace_context() -> Optional[Dict[str, str]]:
    """
    Retrieve the tracing context for the Ray Serve application if running within Anyscale.
    This function attempts to import and call the `get_trace_context` function from the
    `ray.anyscale.serve.utils` module, which is only available when the application is
    deployed within Anyscale. If the import fails (i.e., the application is not running
    within Anyscale), the function returns an empty dictionary.
    Returns:
        dict: The trace context if running within Anyscale; otherwise, an empty dictionary.
    """
    try:
        from ray.anyscale.serve.utils import get_trace_context
        return get_trace_context()
    except ImportError:
        return {}  # Not running in Anyscale.


app = FastAPI()
FastAPIInstrumentor().instrument_app(app)


@serve.deployment
@serve.ingress(app)
class HelloWorld:
    @app.get("/")
    def hello(self):
        # Create a new span that is associated with the current trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
                "application_span", context=get_serve_trace_context()
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

            # Return message
            return "Hello world!"


app = HelloWorld.bind()
