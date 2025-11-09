# Tracing guide

This guide provides three tutorials on how to add OpenTelemetry tracing for a Ray Serve applications in an
Anyscale Service. The first tutorial provides a quick start on how to collect Ray Serve traces and view them in the Ray logs. The second tutorial provides a more in-depth example on how to instrument your application. The third details how to export traces to a tracing backend.

:::note
Ray >=2.47 is the minimum version required to use distributed tracing with FastAPI and the FastAPIInstrumentor.
:::

Note that by default, each request handled by the Serve application exports a trace that provides observability of the full span of the request.

## Getting started

## Quick start
Set the `tracing_config` in the service config.

```yaml title=examples/quick-start/default_tracing_service.yaml
# examples/quick-start/default_tracing_service.yaml
name: default-tracing-service
working_dir: https://github.com/anyscale/tracing-example/archive/refs/heads/main.zip#subdirectory=examples/quick-start
image_uri: anyscale/ray:2.51.0-slim-py311
requirements:
  - opentelemetry-api==1.26.0
  - opentelemetry-sdk==1.26.0
  - opentelemetry-exporter-otlp==1.26.0
  - opentelemetry-exporter-otlp-proto-grpc==1.26.0
  - opentelemetry-instrumentation==0.47b0
  - opentelemetry-instrumentation-asgi==0.47b0
  - opentelemetry-instrumentation-fastapi==0.47b0
applications:
  - route_prefix:  '/'
    import_path: default_serve_hello:app
    runtime_env: {}
tracing_config:
  enabled: True
  sampling_ratio: 1.0

```

Deploy the service using the following command.

```bash
anyscale service deploy -f examples/quick-start/default_tracing_service.yaml
```

After querying your application, Anyscale exports traces to the `/tmp/ray/session_latest/logs/serve/spans/` folder on instances with active replicas.

```bash
cat /tmp/ray/session_latest/logs/serve/spans/proxy*.json
```

```json
{
    "name": "route_to_replica HelloWorld __call__",
    "context": {
        "trace_id": "0xf829758dcca0cea68128174d71d4f5f2",
        "span_id": "0x1f2154f825a3b21c",
        "trace_state": "[]"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": "0x771cf15c3798baf1",
    "start_time": "2025-11-10T00:53:16.648448Z",
    "end_time": "2025-11-10T00:53:16.654364Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "request_id": "59ea3006-b53e-4460-882a-f576d43b9055",
        "deployment": "HelloWorld",
        "app": "default",
        "call_method": "__call__",
        "route": "/",
        "multiplexed_model_id": "",
        "is_streaming": true,
        "is_http_request": true,
        "is_grpc_request": false,
        "resource.name": "route_to_replica HelloWorld __call__",
        "http.method": "__call__",
        "http.route": "/"
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.34.1",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
{
    "name": "proxy_http_request HelloWorld GET /",
    "context": {
        "trace_id": "0xf829758dcca0cea68128174d71d4f5f2",
        "span_id": "0x771cf15c3798baf1",
        "trace_state": "[]"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": null,
    "start_time": "2025-11-10T00:53:16.647830Z",
    "end_time": "2025-11-10T00:53:16.657576Z",
    "status": {
        "status_code": "OK"
    },
    "attributes": {
        "request_id": "59ea3006-b53e-4460-882a-f576d43b9055",
        "deployment": "HelloWorld",
        "app": "default",
        "request_type": "http",
        "request_method": "GET",
        "request_route_path": "/",
        "resource.name": "proxy_http_request HelloWorld GET /",
        "http.method": "GET",
        "http.status_code": 200,
        "http.route": "/"
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.34.1",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
```

## Instrumenting a Serve application

This tutorial provides guidance on how to instrument a Serve app with custom tracing and third party OpenTelemetry compatible instrumentors.

The first step is augmenting the Serve application with OpenTelemetry traces and the FastAPIInstrumentor.

```python title=examples/instrumented/serve_hello.py
# examples/instrumented/serve_hello.py
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from ray import serve
from ray.anyscale.serve._private.tracing_utils import get_trace_context


def build_fastapi_app():
    app = FastAPI()
    FastAPIInstrumentor().instrument_app(app)
    return app


@serve.deployment
@serve.ingress(build_fastapi_app)
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

```

Next, define the service configuration with a service YAML.

```yaml title=examples/instrumented/tracing_service.yaml
# examples/instrumented/tracing_service.yaml
name: tracing-service
working_dir: https://github.com/anyscale/tracing-example/archive/refs/heads/main.zip#subdirectory=examples/instrumented
image_uri: anyscale/ray:2.51.0-slim-py311
requirements:
  - opentelemetry-api==1.26.0
  - opentelemetry-sdk==1.26.0
  - opentelemetry-exporter-otlp==1.26.0
  - opentelemetry-exporter-otlp-proto-grpc==1.26.0
  - opentelemetry-instrumentation==0.47b0
  - opentelemetry-instrumentation-asgi==0.47b0
  - opentelemetry-instrumentation-fastapi==0.47b0
applications:
  - name: my_app
    route_prefix:  '/'
    import_path: serve_hello:app
    runtime_env: {}
tracing_config:
  enabled: True
  sampling_ratio: 1.0

```

To deploy the service, we can run the following command.

```bash
anyscale service deploy -f examples/instrumented/tracing_service.yaml
```

After querying your application, Anyscale exports traces to the `/tmp/ray/session_latest/logs/serve/spans/` folder on instances with active replicas.

```bash
cat /tmp/ray/session_latest/logs/serve/spans/replica*.json
```

```json
{
    "name": "application_span",
    "context": {
        "trace_id": "0x2a57f560a3e6c8c33f1886b9d2cbb748",
        "span_id": "0xfe0bd8218823708f",
        "trace_state": "[]"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0x5f91ee3b05879412",
    "start_time": "2025-11-10T01:00:09.994951Z",
    "end_time": "2025-11-10T01:00:09.994983Z",
    "status": {
        "status_code": "OK"
    },
    "attributes": {
        "deployment": "HelloWorld",
        "replica_id": "rba21irc"
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.38.0",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
{
    "name": "GET / http send",
    "context": {
        "trace_id": "0x2a57f560a3e6c8c33f1886b9d2cbb748",
        "span_id": "0x39bf09e57e96de6d",
        "trace_state": "[]"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0x5f91ee3b05879412",
    "start_time": "2025-11-10T01:00:09.995322Z",
    "end_time": "2025-11-10T01:00:09.995355Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "asgi.event.type": "http.response.start",
        "http.status_code": 200
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.38.0",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
{
    "name": "GET / http send",
    "context": {
        "trace_id": "0x2a57f560a3e6c8c33f1886b9d2cbb748",
        "span_id": "0x6797ff778d734b7f",
        "trace_state": "[]"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0x5f91ee3b05879412",
    "start_time": "2025-11-10T01:00:09.995595Z",
    "end_time": "2025-11-10T01:00:09.995611Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "asgi.event.type": "http.response.body"
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.38.0",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
{
    "name": "GET /",
    "context": {
        "trace_id": "0x2a57f560a3e6c8c33f1886b9d2cbb748",
        "span_id": "0x5f91ee3b05879412",
        "trace_state": "[]"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0xea8f9f83ab30915e",
    "start_time": "2025-11-10T01:00:09.994684Z",
    "end_time": "2025-11-10T01:00:09.995897Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "http.scheme": "https",
        "http.host": "10.0.17.185:8000",
        "net.host.port": 8000,
        "http.flavor": "1.1",
        "http.target": "/",
        "http.url": "https://fastapi-instrumented-tracing-service-jgz99.cld-kvedzwag2qa8i5bj.s.anyscaleuserdata.com/",
        "http.method": "GET",
        "http.server_name": "fastapi-instrumented-tracing-service-jgz99.cld-kvedzwag2qa8i5bj.s.anyscaleuserdata.com",
        "http.user_agent": "curl/8.7.1",
        "net.peer.ip": "157.131.214.156",
        "http.route": "/",
        "http.status_code": 200
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.38.0",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
{
    "name": "replica_handle_request HelloWorld __call__",
    "context": {
        "trace_id": "0x2a57f560a3e6c8c33f1886b9d2cbb748",
        "span_id": "0xea8f9f83ab30915e",
        "trace_state": "[]"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": "0x6dbfcda15dbadb71",
    "start_time": "2025-11-10T01:00:09.993521Z",
    "end_time": "2025-11-10T01:00:09.997203Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "resource.name": "replica_handle_request HelloWorld __call__",
        "request_id": "379879bb-da36-46d8-8665-d29ab2f0e4c1",
        "replica_id": "rba21irc",
        "deployment": "HelloWorld",
        "app": "my_app",
        "call_method": "__call__",
        "route": "/",
        "multiplexed_model_id": "",
        "is_streaming": true,
        "http.method": "GET",
        "http.status_code": "200",
        "http.route": "/"
    },
    "events": [],
    "links": [],
    "resource": {
        "attributes": {
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.38.0",
            "service.name": "unknown_service"
        },
        "schema_url": ""
    }
}
```

## Defining a custom exporter

This tutorial provides guidance on how to export the OpenTelemetry traces to a tracing backend. This will require defining an OpenTelemetry compatible exporter inside a Docker image and referencing that exporter inside the service YAML.

### Build an image containing an OpenTelemetry compatible exporter

To export traces to a tracing backend, we need to define a tracing exporter function in `exporter_hc.py`. The tracing exporter needs to be a Python function that takes no arguments and returns a list of type `SpanProcessor`. Note, you can configure this function to return several span processors so traces are exported to multiple backends.

```python title=examples/exporter/exporter_hc.py
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from typing import List
from opentelemetry.sdk.trace import SpanProcessor


def honeycomb_span_processors() -> List[SpanProcessor]:
    # Reads OTEL_* env vars; no arguments needed
    return [BatchSpanProcessor(OTLPSpanExporter())]

```

Then define a Dockerfile and environment dependencies.

```
# examples/exporter/requirements.txt
asgiref==3.8.1
deprecated==1.2.14
importlib-metadata==8.2.0
opentelemetry-api==1.26.0
opentelemetry-exporter-otlp-proto-http==1.26.0
opentelemetry-instrumentation==0.47b0
opentelemetry-instrumentation-asgi==0.47b0
opentelemetry-instrumentation-fastapi==0.47b0
opentelemetry-sdk==1.26.0
opentelemetry-semantic-conventions==0.47b0
opentelemetry-util-http==0.47b0
statsd==4.0.1
zipp==3.20.0

```

```Dockerfile title=examples/exporter/Dockerfile
# Use Anyscale base image
FROM anyscale/ray:2.51.0-slim-py311

# Copy the requirements file into the Docker image
COPY requirements.txt .

# Install all dependencies specified in requirements.txt
RUN pip install --no-cache-dir  --no-dependencies -r requirements.txt

# Copy exporter file and application definitions into the Docker image
COPY exporter_hc.py /home/ray/exporter_hc.py
COPY serve_hello.py /home/ray/serve_hello.py

# Set environment variables for OTLP exporter
ENV OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io"
ENV OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=your-api-key"
ENV OTEL_SERVICE_NAME="my-service-name"

# Add working directory into python path so they are importable
ENV PYTHONPATH=/home/ray

```


After defining the Dockerfile, build and push the Docker image with the following commands.

```bash
# build the Docker image
docker build examples/exporter -t my-registry/my-image:tag

# push the Docker image to your registry
docker push my-registry/my-image:tag
```

Next, define the service configuration with a service YAML and `image_uri` that points to the image. Also, define the module in `exporter_import_path` to load the span exporters when tracing is setup

```yaml title=examples/exporter/tracing_service_with_exporter.yaml
# examples/exporter/tracing_service_with_exporter.yaml
name: tracing-service-with-exporter
image_uri: <IMAGE_URI>
applications:
  - name: my_app
    route_prefix:  '/'
    import_path: serve_hello:app
    runtime_env: {}
tracing_config:
  exporter_import_path: exporter_hc:honeycomb_span_processors
  enabled: True
  sampling_ratio: 1.0

```

To deploy the service, we can run the following command.

```bash
anyscale service deploy -f examples/exporter/tracing_service_with_exporter.yaml
```

After querying your application, Anyscale exports traces to the backend defined in `examples/exporter/exporter_hc.py`.

## Propagate traces between services

To properly propagate traces between upstream and downstream services, you need to
ensure that `traceparent` is passed in the headers of the request.
`TraceContextTextMapPropagator().inject()` serializes the trace context and add
the proper `traceparent` to the header object. The following code snippet
demonstrates how to propagate traces between two services.

```python
# examples/upstream-downstream/serve_call_external_service.py
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
        # Create a new span associated with the current trace.
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
            # Update the span attributes and status.
            attributes = {
                "deployment": replica_context.deployment,
                "replica_id": replica_context.replica_id.unique_id
            }
            span.set_attributes(attributes)
            span.set_status(
                Status(status_code=StatusCode.OK)
            )

            # Return message.
            return {
                "upstream_message": "Hello world from UpstreamApp!",
                "downstream_message": resp.text,
            }


@serve.deployment
class DownstreamApp:
    async def __call__(self):
        # Create a new span associated with the current trace.
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
                "downstream_application_span", context=get_trace_context()
        ) as span:
            replica_context = serve.get_replica_context()
            # Update the span attributes and status.
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

            # Return message.
            return "Hello world from DownstreamApp!"


upstream_app = UpstreamApp.bind()
downstream_app = DownstreamApp.bind()

```

Define the service configuration with a service YAML like below. This service
creates two endpoints, one for the upstream service and one for the downstream service.
The traces continue to export to the backend defined in `examples/exporter/exporter_hc.py` from the
previous section.

```yaml title=examples/upstream-downstream/tracing_upstream_downstream_service.yaml
# examples/upstream-downstream/tracing_upstream_downstream_service.yaml
name: tracing-upsteam-downstream-service
image_uri: <IMAGE_URI>
applications:
  - name: app
    route_prefix: /
    import_path: serve_call_external_service:upstream_app
    runtime_env: {}
  - name: app2
    route_prefix: /downstream
    import_path: serve_call_external_service:downstream_app
    runtime_env: {}
tracing_config:
  exporter_import_path: exporter_hc:honeycomb_span_processors
  enabled: True
  sampling_ratio: 1.0


```

To deploy the service, run the following command:

```bash
anyscale service deploy -f examples/upstream-downstream/tracing_upstream_downstream_service.yaml
```

After querying your application, Anyscale exports traces to Honeycomb. The spans are
linked properly between the upstream and downstream services.

## Developing on Workspaces
As of Ray 2.40.0, tracing can only be enabled on Workspaces through setting the
environment variable `ANYSCALE_TRACING_EXPORTER_IMPORT_PATH` to a valid exporter
function. In order to start developing tracing on Workspaces, you need to define this
environment variable in after the Workspace is started.

Start a workspace with the image of your choice (i.e.
`anyscale/ray:2.51.0-slim-py311`). Then, go to the "Dependencies" tab and add
`ANYSCALE_TRACING_EXPORTER_IMPORT_PATH=exporter_dev:debug_span_processor` to the
Environment Variables section. You would need to terminate and restart the workspace to
have this environment variable take effect.

Once the workspace is restarted, define the exporter function in a `exporter_dev.py`
file like below. This exporter function will be used to export traces to the console
for quickly visualize the attributes on the traces.

```python title=examples/exporter/exporter_dev.py
# examples/exporter/exporter_dev.py
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace import SpanProcessor
from typing import List


def debug_span_processor() -> List[SpanProcessor]:
    return [SimpleSpanProcessor(ConsoleSpanExporter())]

```

And take the same `examples/instrumented/serve_hello.py` file from the previous section.

Start the application with the following command.

```bash
serve run examples.instrumented.serve_hello:app
```

Open another terminal and run the following command to query the application.

```bash
curl http://localhost:8000/
```

You would see the logs in the console as well as the logs tab with the tracing info.

```bash
(ProxyActor pid=4282) {
(ProxyActor pid=4282)     "name": "proxy_route_to_replica",
(ProxyActor pid=4282)     "context": {
(ProxyActor pid=4282)         "trace_id": "0xd25e4255f28c5d0f21a50a3053cf331a",
(ProxyActor pid=4282)         "span_id": "0x78ee649d2357cd56",
(ProxyActor pid=4282)         "trace_state": "[]"
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "kind": "SpanKind.SERVER",
(ProxyActor pid=4282)     "parent_id": "da6d23cabff76185",
(ProxyActor pid=4282)     "start_time": "2024-12-30T23:47:44.155435Z",
(ProxyActor pid=4282)     "end_time": "2024-12-30T23:47:44.166501Z",
(ProxyActor pid=4282)     "status": {
(ProxyActor pid=4282)         "status_code": "OK"
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "attributes": {
(ProxyActor pid=4282)         "request_id": "7bda8dd6-9299-42ce-b23b-ac059d03254e",
(ProxyActor pid=4282)         "deployment": "HelloWorld",
(ProxyActor pid=4282)         "app": "default",
(ProxyActor pid=4282)         "call_method": "__call__",
(ProxyActor pid=4282)         "route": "/",
(ProxyActor pid=4282)         "multiplexed_model_id": "",
(ProxyActor pid=4282)         "is_streaming": true,
(ProxyActor pid=4282)         "is_http_request": true,
(ProxyActor pid=4282)         "is_grpc_request": false
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "events": [],
(ProxyActor pid=4282)     "links": [],
(ProxyActor pid=4282)     "resource": {
(ProxyActor pid=4282)         "telemetry.sdk.language": "python",
(ProxyActor pid=4282)         "telemetry.sdk.name": "opentelemetry",
(ProxyActor pid=4282)         "telemetry.sdk.version": "1.1.0",
(ProxyActor pid=4282)         "service.name": "unknown_service"
(ProxyActor pid=4282)     }
(ProxyActor pid=4282) }
(ProxyActor pid=4282) {
(ProxyActor pid=4282)     "name": "proxy_http_request",
(ProxyActor pid=4282)     "context": {
(ProxyActor pid=4282)         "trace_id": "0xd25e4255f28c5d0f21a50a3053cf331a",
(ProxyActor pid=4282)         "span_id": "0xda6d23cabff76185",
(ProxyActor pid=4282)         "trace_state": "[]"
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "kind": "SpanKind.SERVER",
(ProxyActor pid=4282)     "parent_id": null,
(ProxyActor pid=4282)     "start_time": "2024-12-30T23:47:44.154995Z",
(ProxyActor pid=4282)     "end_time": "2024-12-30T23:47:44.175150Z",
(ProxyActor pid=4282)     "status": {
(ProxyActor pid=4282)         "status_code": "OK"
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "attributes": {
(ProxyActor pid=4282)         "request_id": "7bda8dd6-9299-42ce-b23b-ac059d03254e",
(ProxyActor pid=4282)         "deployment": "HelloWorld",
(ProxyActor pid=4282)         "app": "default",
(ProxyActor pid=4282)         "request_type": "http",
(ProxyActor pid=4282)         "request_method": "GET",
(ProxyActor pid=4282)         "request_route_path": "/"
(ProxyActor pid=4282)     },
(ProxyActor pid=4282)     "events": [],
(ProxyActor pid=4282)     "links": [],
(ProxyActor pid=4282)     "resource": {
(ProxyActor pid=4282)         "telemetry.sdk.language": "python",
(ProxyActor pid=4282)         "telemetry.sdk.name": "opentelemetry",
(ProxyActor pid=4282)         "telemetry.sdk.version": "1.1.0",
(ProxyActor pid=4282)         "service.name": "unknown_service"
(ProxyActor pid=4282)     }
(ProxyActor pid=4282) }
(ServeReplica:default:HelloWorld pid=4347)     "name": "application_span",
(ServeReplica:default:HelloWorld pid=4347)     "kind": "SpanKind.INTERNAL",
(ServeReplica:default:HelloWorld pid=4347)         "replica_id": "5w6y35rx"
(ServeReplica:default:HelloWorld pid=4347)     "name": "replica_handle_request",
(ServeReplica:default:HelloWorld pid=4347)         "replica_id": "5w6y35rx",
(ServeReplica:default:HelloWorld pid=4347)         "is_streaming": true
(ServeReplica:default:HelloWorld pid=4347) INFO 2024-12-30 23:47:44,173 default_HelloWorld 5w6y35rx 7bda8dd6-9299-42ce-b23b-ac059d03254e -- GET / 200 8.5ms
```

## Export traces to Datadog
You can use Datadog agent to export traces to their platform. This doc does not cover
how to set up Datadog agents. You can find more information on the
[DataDog Agent](https://docs.datadoghq.com/agent/). The idea is to have dd agent running
on as the sidecar on the same machine as the Ray Serve application and have the exporter
function export the traces to the ports which the Datadog agent is listing on.

These are some pointers to get you started:

#### Shell script to start a local Datadog agent
```bash
#!/bin/bash

set -x

export DD_API_KEY=TOTALLY_FAKE_API_KEY
export DD_SITE=datadoghq.com
docker run --rm -d --cgroupns host --pid host --name dd-agent \
    -p 8126:8126 \
    -p 4318:4318 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /proc/:/host/proc/:ro \
    -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
    -e DD_SITE=${DD_SITE} \
    -e DD_API_KEY=${DD_API_KEY} \
    -e DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_HTTP_ENDPOINT=0.0.0.0:4318 \
    gcr.io/datadoghq/agent:7
```

#### Useful environment variables to set in the Docker image
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://0.0.0.0:4318
OTEL_LOG_LEVEL=DEBUG
OTEL_SERVICE_NAME=my-service-name
ANYSCALE_TRACING_EXPORTER_IMPORT_PATH=exporter_dd:anyscale_span_processors
```

#### Exporter function to export traces to Datadog agent
```python title=examples/exporter/exporter_dd.py
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

```
