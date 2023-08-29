FROM python:3.8 AS base

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_QUIET 2
ENV PIP_USER 1
ENV PYTHONUSERBASE /djangoenv
ENV PATH="$PYTHONUSERBASE/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        jq \
        ffmpeg \
        ghostscript \
        imagemagick \
        libmagic-dev \
        webp \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3003
RUN EXIFTOOL_VERSION="$(wget -qO- https://api.github.com/repos/exiftool/exiftool/tags | jq -r '.[0].name')" \
    EXIFTOOL_FILENAME=exiftool-"${EXIFTOOL_VERSION}" \
    && wget --progress=dot:giga https://github.com/exiftool/exiftool/archive/refs/tags/"${EXIFTOOL_VERSION}".tar.gz -O "${EXIFTOOL_FILENAME}".tar.gz \
    && tar xvf "${EXIFTOOL_FILENAME}".tar.gz \
    && cd "${EXIFTOOL_FILENAME}"/ \
    && perl Makefile.PL \
    && make test \
    && make install \
    && cd .. \
    && rm -rf "${EXIFTOOL_FILENAME}"*

# hadolint ignore=DL3059
RUN mkdir /logs
VOLUME /logs

# RUN mkdir -p /django/assets
# VOLUME /django/assets

WORKDIR /django

RUN pip install --upgrade pip==23.2.1
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8200


FROM base as dev

# to ensure pip-sync is also working in docker dev setup we need to overwrite requirements.txt
COPY requirements-dev.txt requirements.txt
RUN pip-sync

CMD ["python", "manage.py", "runserver", "0.0.0.0:8200"]


FROM base as prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "portfolio.wsgi", "-c", "/django/gunicorn-conf.py"]
