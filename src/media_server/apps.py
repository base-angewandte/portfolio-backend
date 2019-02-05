import django_rq
from django.apps import AppConfig


class MediaServerConfig(AppConfig):
    name = 'media_server'

    def ready(self):
        scheduler = django_rq.get_scheduler('high')

        # delete any existing jobs in the scheduler when the app starts up
        for job in scheduler.get_jobs():
            job.delete()

        # tasks
        scheduler.cron('5 2 * * *', 'media_server.models.repair')
