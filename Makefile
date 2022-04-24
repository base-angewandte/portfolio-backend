include .env
export


start:
	docker-compose pull --ignore-pull-failures
	docker-compose build --no-cache --pull portfolio-django
	docker-compose up -d --build

stop:
	docker-compose down

restart:
	docker-compose restart

git-update:
	if [ "$(shell whoami)" != "base" ]; then sudo -u base git pull; else git pull; fi

init:
	docker-compose exec portfolio-django bash -c "pip-sync && python manage.py migrate"

init-rq:
	docker-compose exec portfolio-rq-worker-1 bash -c "pip-sync && python manage.py migrate"
	docker-compose exec portfolio-rq-worker-2 bash -c "pip-sync && python manage.py migrate"
	docker-compose exec portfolio-rq-worker-3 bash -c "pip-sync && python manage.py migrate"
	docker-compose exec portfolio-rq-scheduler bash -c "pip-sync && python manage.py migrate"

init-static:
	docker-compose exec portfolio-django bash -c "python manage.py collectstatic --noinput"

cleanup:
	docker-compose exec portfolio-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

build-portfolio:
	docker-compose build --pull portfolio-django

restart-gunicorn:
	docker-compose exec portfolio-django bash -c 'kill -HUP `cat /var/run/django.pid`'

restart-rq:
	docker-compose restart portfolio-rq-worker-1 portfolio-rq-worker-2 portfolio-rq-worker-3 portfolio-rq-scheduler

update: git-update init init-rq init-static restart-gunicorn restart-rq build-docs

start-dev:
	docker-compose pull --ignore-pull-failures
	docker-compose up -d \
		portfolio-redis \
		portfolio-postgres \
		portfolio-lool

start-dev-docker:
	docker-compose pull --ignore-pull-failures
	docker-compose build --no-cache --pull portfolio-django
	docker-compose up -d \
		portfolio-redis \
		portfolio-postgres \
		portfolio-lool \
		portfolio-django
	docker logs -f portfolio-django

clear-entries:
	docker-compose exec portfolio-django bash -c "python manage.py clear_entries"

build-docs:
	docker build -t portfolio-docs ./docker/docs
	docker run -it --rm -v `pwd`/docs:/docs -v `pwd`/src:/src portfolio-docs bash -c "make clean html"

pip-compile:
	pip-compile src/requirements.in
	pip-compile src/requirements-dev.in

pip-compile-upgrade:
	pip-compile src/requirements.in --upgrade
	pip-compile src/requirements-dev.in --upgrade
