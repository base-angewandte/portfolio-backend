# Installation Guide

## Development

There are two supported ways to start the development server:

1. Start only the auxiliary services (database, redis, etc.) in docker
   but start the django dev server locally in your virtual env. This
   is the preferred way if you actively develop this application.

2. Start everything inside docker containers. This is the "easy" way
   to start a dev server and fiddle around with it, hot reloading included.
   But you will not have the local pre-commit setup.

In both cases there are some common steps to follow:

* Make sure you have `make` installed (e.g. with `sudo apt install make`
  for Debian based distributions)

* [Install docker and docker-compose](https://docs.docker.com/get-docker/)
  for your system

* Clone git repository and checkout branch `develop`:

    ```bash
    git clone https://github.com/base-angewandte/portfolio-backend.git
    cd portfolio-backend
    git checkout develop
    ```

* Check and adapt settings (see [Configuration](./configuration.md) for further details about the configuration possibilities):

    ```bash
    # env
    cp env-skel .env
    vi .env
    
    # django env
    cp ./src/portfolio/env-skel ./src/portfolio/.env
    vi ./src/portfolio/.env
    ```

* Create docker-compose override file:

    ```bash
    cp docker-compose.override.dev.yml docker-compose.override.yml
    ```

Now, depending on which path you want to go, take one of the following two
subsections.

### Everything inside docker

* Make sure that the `DOCKER` variable in `./src/portfolio/.env` is set to
  `TRUE`. Otherwise Django will assume that postgres and redis are accessible
  on localhost ports.

* Now create the docker-compose override file:

    ```bash
    cp docker-compose.override.dev-docker.yml docker-compose.override.yml
    ```

* Start everything:

    ```bash
    make start-dev-docker
    ```

  Alternatively, if make is not installed on your system yet, you can
  also just use `docker-compose` directly:

    ```bash
    docker-compose up -d --build portfolio-redis portfolio-postgres portfolio-lool portfolio-django
    ```

  If you did start the service with the `docker-compose` instead of `make`, you
  might want to do the following to also get Django's debug output:

    ```bash
    docker logs -f portfolio-django-dev
    ```

  To stop all services again, use `make stop` or `docker-compose down`.

### The full developer setup

* Install latest python 3.7 and create virtualenv e.g. via [`pyenv`](https://github.com/pyenv/pyenv) and [`pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv)

* Install pip-tools and requirements in your virtualenv:

    ```bash
    pip install pip-tools
    pip-sync src/requirements-dev.txt
    ```

* Install pre-commit hooks:

    ```bash
    pre-commit install
    ```

* Install required packages for media conversion:
    
    * Debian based Linux distributions
        ```bash
        sudo apt install bc \
          ffmpeg \
          ghostscript \
          imagemagick \
          libmagic-dev \
          webp \
          exiftool
        ```
  
    * macOS (Installation recommended via [homebrew](https://brew.sh/))
        ```bash
        brew install ffmpeg ghostscript imagemagick webp exiftool
        ```

* Start required services:

    ```bash
    make start-dev
    ```
    
* Run migration:

    ```bash
    cd src
    python manage.py migrate
    ```

* Start development server:

    ```bash
    python manage.py runserver 8200
    ```

    **Notes:**

    * If you are working **on a system with non-US/UK locales** you might use a
      number format that uses `,` as decimal separator rather than `.`. In that
      case **audio and video conversions will fail** due to an error when `printf` is
      used to format the duration. This should not affect the containerised dev
      and production setup. To work around this, set the `LC_NUMERIC` environment
      variable to `en_US.UTF-8`, e.g. by starting the dev server with the following
      command:

      ```bash
      LC_NUMERIC="en_US.UTF-8" python manage.py runserver 8200
      ```

## Production

* Update package index:

    ```bash
    # RHEL
    sudo yum update

    # Debian
    sudo apt-get update
    ```

* Install docker and docker-compose

* Create and change to user `base`

* Create and change to `/opt/base`

* Clone git repository and checkout branch `master`:

    ```bash
    git clone https://github.com/base-angewandte/portfolio-backend.git
    cd portfolio-backend
    git checkout master
    ```

* Check and adapt settings (see [Configuration](./configuration.md) for further details about the configuration possibilities):

    ```bash
    # env
    cp env-skel .env
    vi .env
    
    # django env
    cp ./src/portfolio/env-skel ./src/portfolio/.env
    vi ./src/portfolio/.env
    ```

* Use `Makefile` to initialize and run project:

    ```bash
    make start init init-static restart-gunicorn
    ```

* Install nginx and configure it accordingly
