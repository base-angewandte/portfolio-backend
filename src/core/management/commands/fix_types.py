from progressbar import progressbar
from titlecase import titlecase

from django.core.management.base import BaseCommand

from core.models import Entry


class Command(BaseCommand):
    help = 'Fix English labels in types'

    def handle(self, *args, **options):
        for e in progressbar(Entry.objects.all()):
            if e.type:
                label_titlecase = titlecase(e.type['label']['en'])
                if label_titlecase != e.type['label']['en']:
                    e.type['label']['en'] = label_titlecase
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed types'))
