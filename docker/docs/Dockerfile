FROM python:3.8

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /tmp/requirements.txt

RUN pip install -qq --upgrade --no-cache-dir pip==21.1.3 \
    && pip install -qq --disable-pip-version-check --no-cache-dir -r /tmp/requirements.txt

WORKDIR /docs
VOLUME /docs
