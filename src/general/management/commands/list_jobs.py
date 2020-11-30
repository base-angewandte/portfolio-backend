import django_rq

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List rq-scheduler jobs'

    def handle(self, *args, **options):
        scheduler = django_rq.get_scheduler()

        for job in scheduler.get_jobs():
            self.stdout.write(f'{job}')
