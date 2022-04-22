from progressbar import progressbar

from django.core.management.base import BaseCommand

from core.models import Entry


class Command(BaseCommand):
    help = 'Fix invalid contributors'

    def handle(self, *args, **options):
        for e in progressbar(Entry.objects.all()):
            if e.data and e.data.get('contributors'):
                need_to_save = False
                contributors = e.data['contributors']
                for _idx, contributor in enumerate(contributors):
                    if not contributor.get('label'):
                        # need_to_save = True
                        self.stdout.write(e.pk)
                        if contributor.get('source'):
                            self.stdout.write(contributor.get('source'))
                        else:
                            self.stdout.write(str(contributor))
                if need_to_save:
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed contributors'))
