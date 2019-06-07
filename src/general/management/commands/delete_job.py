import django_rq
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Delete the specified rq-scheduler job'

    def add_arguments(self, parser):
        parser.add_argument('job_id', nargs='+', type=str)

    def handle(self, *args, **options):
        scheduler = django_rq.get_scheduler()

        for job_id in options['job_id']:
            if job_id not in scheduler:
                raise CommandError('Job "{}" does not exist'.format(job_id))

            scheduler.cancel(job_id)

            self.stdout.write(self.style.SUCCESS('Successfully deleted job "{}"'.format(job_id)))
