from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from ray import serve
from ray.anyscale.serve._private.tracing_utils import get_trace_context


def build_fastapi_app():
    app = FastAPI()
    FastAPIInstrumentor().instrument_app(app)

    @app.get("/")
    async def hello():
        # Create a new span that is associated with the current trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "application_span", context=get_trace_context()
        ) as span:
            replica_context = serve.get_replica_context()
            # Update the span attributes and status
            attributes = {
                "deployment": replica_context.deployment,
                "replica_id": replica_context.replica_id.unique_id,
            }
            span.set_attributes(attributes)
            span.set_status(Status(status_code=StatusCode.OK))

            # Return message
            return "Hello world!"

    return app


@serve.deployment
@serve.ingress(build_fastapi_app)
class HelloWorld:
    """Main serve deployment."""


app = HelloWorld.bind()
