FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        ffmpeg \
        libmagic-dev \
        libimage-exiftool-perl \
        cmake \
        gtk-doc-tools \
        ghostscript \
        libjpeg62-turbo-dev \
        libtiff5-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        libharfbuzz-dev \
        libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

ADD pillow_depends /depends
RUN cd /depends && ./install_openjpeg.sh && ./install_imagequant.sh && ./install_raqm.sh

RUN mkdir /logs
VOLUME /logs

# RUN mkdir -p /django/assets
# VOLUME /django/assets

WORKDIR /django

RUN pip install --upgrade pip==19.1.1
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD rainbow-saddle --pid /var/run/django.pid gunicorn portfolio.wsgi -w 3 -b :8200 -t 300 --max-requests 1000 --log-level=info --access-logfile=/logs/gunicorn.access.log --error-logfile=/logs/gunicorn.error.log

EXPOSE 8200
