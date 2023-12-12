import csv
import operator
from functools import reduce

from progressbar import progressbar

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import translation

from core.models import Entry
from core.schemas import get_active_schemas
from core.skosmos import get_preflabel_lazy


class Command(BaseCommand):
    help = 'Export all published entries'

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, nargs='?', default=-1)
        parser.add_argument('--lang', type=str)

    def handle(self, *args, **options):
        year = options['year']

        if year == -1:
            year = 'all'

        lang = options['lang'] or 'en'

        if lang in settings.LANGUAGES_DICT.keys():
            translation.activate(lang)

        lang = translation.get_language()

        def _handle_dict(dct):
            lbl = dct.get('label') or ''
            val = dct.get('value') or ''
            if isinstance(val, list):
                val = _handle_list(val)
            elif isinstance(val, dict) and (val.get('from') or val.get('to')):
                val = '{} - {}'.format(val.get('from') or '', val.get('to') or '')
            elif isinstance(val, str):
                # replace line breaks
                val = ' '.join(val.splitlines())

            return f'{lbl}: {val}'.strip(' :')

        def _handle_list(value):
            lst = []

            for item in value:
                if isinstance(item, dict):
                    lst.append(_handle_dict(item))
                else:
                    lst.append(item)

            return ' | '.join(lst)

        with open(f'export/{year}-published.csv', mode='w') as csvfile:
            csv_writer = csv.writer(
                csvfile,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )
            csv_writer.writerow(
                [
                    'ID',
                    get_preflabel_lazy('title'),
                    get_preflabel_lazy('subtitle'),
                    get_preflabel_lazy('type'),
                    'owner' if lang == 'en' else 'Besitzer',
                    'data' if lang == 'en' else 'Daten',
                ]
            )
            date_filters = []
            date_fields = []
            schemas = get_active_schemas()

            for s in schemas:
                date_fields += s().date_fields

            query = Entry.objects.filter(published=True)

            if year != 'all':
                for df in list(set(date_fields)):
                    date_filters.append({f'data__{df}__icontains': year})
                query = query.filter(
                    reduce(operator.or_, (Q(**x) for x in date_filters))
                )

            for e in progressbar(query):
                data = []
                for d in e.data_display.get('data'):
                    d_label = d.get('label') or ''
                    if isinstance(d.get('value'), list):
                        ld = []
                        for i in d.get('value'):
                            if isinstance(i, dict):
                                ld.append(_handle_dict(i))
                            elif isinstance(i, list):
                                ld.append(_handle_list(i))
                            elif i:
                                ld.append(i)
                        data.append('{}: {}'.format(d_label, ' | '.join(ld)))
                    else:
                        d_value = d.get('value') or ''
                        data.append(f'{d_label}: {d_value}'.strip(' :'))
                csv_writer.writerow(
                    [
                        e.id,
                        e.title,
                        e.subtitle,
                        e.type.get('label').get(lang) if e.type else '',
                        e.owner.get_full_name(),
                        ' // '.join(data),
                    ]
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully exported all published entries')
        )
