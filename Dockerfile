# Use Anyscale base image
FROM anyscale/ray:2.40.0-slim-py310

# Copy the requirements file into the Docker image
COPY requirements.txt .

# Install all dependencies specified in requirements.txt
RUN pip install --no-cache-dir  --no-dependencies -r requirements.txt

# Copy exporter file and application definitions into the Docker image
COPY exporter.py /home/ray/exporter.py
COPY serve_hello.py /home/ray/serve_hello.py
COPY serve_call_external_service.py /home/ray/serve_call_external_service.py
COPY fp.py /home/ray/fp.py

# Set environment variables for Honeycomb exporter
ENV HONEYCOMB_SERVICE_NAME="my-service-name"
ENV HONEYCOMB_WRITE_KEY="xxxxxxxxxxxxxxxxxxxxxx"
ENV HONEYCOMB_DATASET_NAME="my-dataset-name"

# Add working directory into python path so they are importable
ENV PYTHONPATH=/home/ray
