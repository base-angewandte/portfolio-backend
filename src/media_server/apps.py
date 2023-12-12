import django_rq

from django.apps import AppConfig


class MediaServerConfig(AppConfig):
    name = 'media_server'

    def ready(self):
        scheduler = django_rq.get_scheduler('high')

        job_id = '1c80dc0d-b81d-46b0-9c59-d3c2f4da679b'

        if job_id not in scheduler:
            scheduler.cron(
                '5 2 * * *',
                'media_server.models.repair',
                id=job_id,
                timeout=7200,
            )
