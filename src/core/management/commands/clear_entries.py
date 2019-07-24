from progressbar import progressbar

from django.core.management.base import BaseCommand

from core.models import Entry
from general.utils import boolean_input


class Command(BaseCommand):
    help = 'Delete all entries'

    def handle(self, *args, **options):
        b = boolean_input('Are you really sure you want to delete all entries? [y/N] ')
        if b:
            for e in progressbar(Entry.objects.all()):
                e.delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted all entries'))
        else:
            self.stdout.write('Aborted')
