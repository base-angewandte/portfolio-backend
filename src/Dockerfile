FROM python:3.7 AS base

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_QUIET 2
ENV PIP_USER 1
ENV PYTHONUSERBASE /djangoenv
ENV PATH="$PYTHONUSERBASE/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        ffmpeg \
        ghostscript \
        imagemagick \
        libmagic-dev \
        webp \
    && rm -rf /var/lib/apt/lists/*

# hadolint ignore=DL3003
RUN EXIFTOOL_VERSION="$(wget -qO- https://exiftool.org/ver.txt)" \
    && wget --progress=dot:giga https://netix.dl.sourceforge.net/project/exiftool/Image-ExifTool-"${EXIFTOOL_VERSION}".tar.gz \
    && tar xvf Image-ExifTool-"${EXIFTOOL_VERSION}".tar.gz \
    && cd Image-ExifTool-"${EXIFTOOL_VERSION}"/ \
    && perl Makefile.PL \
    && make test \
	&& make install \
	&& cd .. \
	&& rm -rf Image-ExifTool-"${EXIFTOOL_VERSION}"*

# hadolint ignore=DL3059
RUN mkdir /logs
VOLUME /logs

# RUN mkdir -p /django/assets
# VOLUME /django/assets

WORKDIR /django

RUN pip install --upgrade pip==21.1.3
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8200


FROM base as dev

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8200"]


FROM base as prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "portfolio.wsgi", "-c", "/django/gunicorn-conf.py"]
