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

clear-entries:
	docker-compose exec portfolio-django bash -c "python manage.py clear_entries"

pip-compile:
	pip-compile src/requirements.in --output-file src/requirements.txt
	pip-compile src/requirements.in src/requirements-dev.in --output-file src/requirements-dev.txt

pip-compile-upgrade:
	pip-compile src/requirements.in --output-file src/requirements.txt --upgrade
	pip-compile src/requirements.in src/requirements-dev.in --output-file src/requirements-dev.txt --upgrade
