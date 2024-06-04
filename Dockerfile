# Use Anyscale base image
FROM anyscale/ray:2.24.0-slim-py39

# Copy the requirements file into the docker image
COPY requirements.txt .

# Install all dependencies specified in requirements.txt
RUN pip install --no-cache-dir  --no-dependencies -r requirements.txt

# Copy exporter file and application definitions into the docker image
COPY exporter.py /home/ray/exporter.py
COPY serve_hello.py /home/ray/serve_hello.py

# Add working directory into python path so they are importable
ENV PYTHONPATH=/home/ray