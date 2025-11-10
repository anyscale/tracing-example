# Use Anyscale base image
FROM anyscale/ray:2.51.0-slim-py311

# Copy the requirements file into the Docker image
COPY requirements.txt .

# Install all dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy exporter file and application definitions into the Docker image
COPY exporter_hc.py /home/ray/exporter_hc.py
COPY serve_hello.py /home/ray/serve_hello.py
COPY serve_call_external_service.py /home/ray/serve_call_external_service.py

# Set environment variables for OTLP exporter
ENV OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io"
ENV OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=your-api-key"
ENV OTEL_SERVICE_NAME="my-service-name"

# Add working directory into python path so they are importable
ENV PYTHONPATH=/home/ray
