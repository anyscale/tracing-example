FROM anyscale/ray:2.20.0-py39

WORKDIR /home/ray

COPY exporter.py /home/ray/exporter.py

ENV PYTHONPATH=/home/ray
