FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

COPY requirements.txt /tmp/requirements.txt

RUN pip install --upgrade --no-cache-dir pip==21.0.1
RUN pip install --disable-pip-version-check --no-cache-dir -r /tmp/requirements.txt

WORKDIR /docs
VOLUME /docs
