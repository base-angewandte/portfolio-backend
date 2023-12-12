include .env
export

PROJECT_NAME ?= portfolio

include config/base.mk


init-rq:
	docker-compose exec ${PROJECT_NAME}-rq-worker-1 bash -c "pip-sync"
	docker-compose exec ${PROJECT_NAME}-rq-worker-2 bash -c "pip-sync"
	docker-compose exec ${PROJECT_NAME}-rq-worker-3 bash -c "pip-sync"
	docker-compose exec ${PROJECT_NAME}-rq-scheduler bash -c "pip-sync"

cleanup:
	docker-compose exec ${PROJECT_NAME}-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

build-portfolio:
	docker-compose build --pull ${PROJECT_NAME}-django

restart-rq:
	docker-compose restart ${PROJECT_NAME}-rq-worker-1 ${PROJECT_NAME}-rq-worker-2 ${PROJECT_NAME}-rq-worker-3 ${PROJECT_NAME}-rq-scheduler

update-labels:
	docker-compose exec ${PROJECT_NAME}-django python manage.py update_labels

update: git-update init init-rq restart-gunicorn restart-rq build-docs update-labels

start-dev:
	docker-compose pull --ignore-pull-failures
	docker-compose up -d \
		${PROJECT_NAME}-redis \
		${PROJECT_NAME}-postgres \
		${PROJECT_NAME}-clamav \
		${PROJECT_NAME}-lool

start-dev-docker:
	docker-compose pull --ignore-pull-failures
	docker-compose build --no-cache --pull ${PROJECT_NAME}-django
	docker-compose up -d \
		${PROJECT_NAME}-redis \
		${PROJECT_NAME}-postgres \
		${PROJECT_NAME}-clamav \
		${PROJECT_NAME}-lool \
		${PROJECT_NAME}-django
	docker logs -f ${PROJECT_NAME}-django

clear-entries:
	docker-compose exec ${PROJECT_NAME}-django bash -c "python manage.py clear_entries"
