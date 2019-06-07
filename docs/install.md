# Installation guide

## Development

* Install docker and docker-compose for your system

* Clone git repository and checkout branch `develop`:

    ```bash
    git clone https://github.com/base-angewandte/portfolio-backend.git
    cd portfolio-backend
    ```

* Check and adapt settings:

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

* Install latest python 3 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`

* Install pip-tools and requirements in your virtualenv:

    ```bash
    pip install pip-tools
    cd src
    pip-sync
    cd ..
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


## Production

* Update package index:

    ```bash
    # RHEL
    sudo yum update

    # Debian
    sudo apt-get update
    ```

* Install docker and docker-compose

* Change to user `base`

* Change to `/opt/base`

* Clone git repository:

    ```bash
    git clone https://github.com/base-angewandte/portfolio-backend.git
    cd portfolio-backend
    ```

* Check and adapt settings:

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
