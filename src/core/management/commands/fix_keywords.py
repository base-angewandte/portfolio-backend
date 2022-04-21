from progressbar import progressbar

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Entry
from core.skosmos import get_preflabel


class Command(BaseCommand):
    help = 'Fix missing labels or empty objects in keywords'

    def handle(self, *args, **options):
        for e in progressbar(Entry.objects.all()):
            if e.keywords:
                need_to_save = False
                need_to_filter = False
                for idx, kw in enumerate(e.keywords):
                    if not kw.get('label'):
                        need_to_save = True
                        if kw.get('source'):
                            graph, concept = kw['source'].rsplit('/', 1)
                            if 'disciplines' in kw['source']:
                                project = 'disciplines'
                            else:
                                project = settings.VOC_ID
                            e.keywords[idx]['label'] = {
                                'de': get_preflabel(concept, project=project, graph=f'{graph}/', lang='de'),
                                'en': get_preflabel(concept, project=project, graph=f'{graph}/', lang='en'),
                            }
                        else:
                            need_to_filter = True
                if need_to_filter:
                    e.keywords = list(filter(None, e.keywords)) or None
                if need_to_save:
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed keywords'))
