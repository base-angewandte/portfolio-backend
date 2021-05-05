import csv
import operator
from functools import reduce

from progressbar import progressbar

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import translation

from core.models import Entry
from core.schemas import ACTIVE_TUPLES


class Command(BaseCommand):
    help = 'Export all published entries'

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)
        parser.add_argument('--lang', type=str)

    def handle(self, *args, **options):
        year = options['year']
        lang = options['lang'] or 'en'

        if lang in settings.LANGUAGES_DICT.keys():
            translation.activate(lang)

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
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(
                [
                    'ID',
                    'title',
                    'subtitle',
                    'type',
                    'owner',
                    'data',
                ]
            )
            date_filters = []
            date_fields = []
            schemas = []

            for _t, s, _i in ACTIVE_TUPLES:
                schemas.append(s)

            for s in list(set(schemas)):
                date_fields += s().date_fields

            for df in list(set(date_fields)):
                date_filters.append({f'data__{df}__icontains': year})

            for e in progressbar(
                Entry.objects.filter(published=True).filter(reduce(operator.or_, (Q(**x) for x in date_filters)))
            ):
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
                        e.type.get('label').get('de'),
                        e.owner.get_full_name(),
                        ' // '.join(data),
                    ]
                )

        self.stdout.write(self.style.SUCCESS('Successfully exported all published entries'))
