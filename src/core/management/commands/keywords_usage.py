import csv
from collections import Counter
from datetime import date

from progressbar import progressbar
from titlecase import titlecase

from django.core.management.base import BaseCommand

from core.models import Entry
from core.skosmos import get_preflabel


class Command(BaseCommand):
    help = 'Return usage of keywords of published entries'

    def handle(self, *args, **options):
        keywords_list = []
        for e in Entry.objects.filter(published=True):
            if e.keywords:
                for kw in e.keywords:
                    if kw.get('source'):
                        keywords_list.append(kw['source'])
                    else:
                        keywords_list.append(kw['label']['en'])

        counter = Counter(keywords_list)

        today = date.today().strftime('%d-%m-%Y')

        with open(f'export/{today}_keywords_usage.csv', mode='w') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(
                [
                    'count',
                    'source',
                    'label_en',
                    'label_de',
                ]
            )
            for kw, num in progressbar(counter.most_common()):
                if kw.startswith('http'):
                    graph, concept = kw.rsplit('/', 1)
                    if 'disciplines' in kw:
                        project = 'disciplines'
                    else:
                        project = 'basekw'
                    label_en = titlecase(get_preflabel(concept, project=project, graph=f'{graph}/', lang='en'))
                    label_de = get_preflabel(concept, project=project, graph=f'{graph}/', lang='de')

                    csv_writer.writerow(
                        [
                            num,
                            kw,
                            label_en,
                            label_de,
                        ]
                    )
                else:
                    csv_writer.writerow(
                        [
                            num,
                            '',
                            kw,
                            kw,
                        ]
                    )

        self.stdout.write(self.style.SUCCESS('Successfully exported keywords usage'))
