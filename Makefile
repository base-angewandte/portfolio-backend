include .env
export


start:
	docker-compose up -d --build

stop:
	docker-compose down

restart:
	docker-compose restart

git-update:
	if [ "$(shell whoami)" != "base" ]; then sudo -u base git pull; else git pull; fi

init:
	docker-compose exec portfolio-django bash -c "pip-sync && python manage.py migrate"

init-static:
	docker-compose exec portfolio-django bash -c "python manage.py collectstatic --noinput"

cleanup:
	docker-compose exec portfolio-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

build-portfolio:
	docker-compose build portfolio-django

restart-gunicorn:
	docker-compose exec portfolio-django bash -c 'kill -HUP `cat /var/run/django.pid`'

restart-rq:
	docker-compose restart portfolio-rq-worker-1 portfolio-rq-worker-2 portfolio-rq-worker-3 portfolio-rq-scheduler

update: git-update init init-static restart-gunicorn restart-rq

start-dev:
	docker-compose up -d --build \
		portfolio-redis \
		portfolio-postgres \
		portfolio-lool

start-dev-docker:
	docker-compose up -d --build \
		portfolio-redis \
		portfolio-postgres \
		portfolio-lool \
		portfolio-django
	docker logs -f portfolio-django-dev

clear-entries:
	docker-compose exec portfolio-django bash -c "python manage.py clear_entries"

pip-compile:
	pip-compile src/requirements.in
	pip-compile src/requirements-dev.in

pip-compile-upgrade:
	pip-compile src/requirements.in --upgrade
	pip-compile src/requirements-dev.in --upgrade
