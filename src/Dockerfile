FROM python:3.7

ENV PYTHONUNBUFFERED 1

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
    && wget https://netix.dl.sourceforge.net/project/exiftool/Image-ExifTool-"${EXIFTOOL_VERSION}".tar.gz \
    && tar xvf Image-ExifTool-"${EXIFTOOL_VERSION}".tar.gz \
    && cd Image-ExifTool-"${EXIFTOOL_VERSION}"/ \
    && perl Makefile.PL \
    && make test \
	&& make install \
	&& cd .. \
	&& rm -rf Image-ExifTool-"${EXIFTOOL_VERSION}"*

RUN mkdir /logs
VOLUME /logs

# RUN mkdir -p /django/assets
# VOLUME /django/assets

WORKDIR /django

RUN pip install --upgrade pip==19.1.1
COPY requirements.txt .
RUN pip install --disable-pip-version-check -r requirements.txt
COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "portfolio.wsgi", "-c", "/django/gunicorn-conf.py"]

EXPOSE 8200
