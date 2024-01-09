from progressbar import progressbar
from titlecase import titlecase

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
                                project = 'basekw'
                            e.keywords[idx]['label'] = {
                                'de': get_preflabel(
                                    concept,
                                    project=project,
                                    graph=f'{graph}/',
                                    lang='de',
                                ),
                                'en': titlecase(
                                    get_preflabel(
                                        concept,
                                        project=project,
                                        graph=f'{graph}/',
                                        lang='en',
                                    )
                                ),
                            }
                        else:
                            need_to_filter = True
                    if kw.get('label'):
                        label_titlecase = titlecase(e.keywords[idx]['label']['en'])
                        if label_titlecase != e.keywords[idx]['label']['en']:
                            need_to_save = True
                            e.keywords[idx]['label']['en'] = label_titlecase
                if need_to_filter:
                    e.keywords = list(filter(None, e.keywords)) or None
                if need_to_save:
                    e.save()
        self.stdout.write(self.style.SUCCESS('Successfully fixed keywords'))
