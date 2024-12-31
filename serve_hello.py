from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from ray import serve
from ray.anyscale.serve._private.tracing_utils import get_trace_context

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class HelloWorld:
    @app.get("/")
    def hello(self):
        # Create a new span that is associated with the current trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "application_span", context=get_trace_context()
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
