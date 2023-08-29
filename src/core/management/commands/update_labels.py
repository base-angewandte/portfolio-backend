from progressbar import progressbar
from titlecase import titlecase

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import JSONField

from core.models import Entry
from core.skosmos import get_preflabel_via_uri


class Command(BaseCommand):
    help = 'Update labels in case they have been changed in the vocabulary'

    # helper variable to prevent unnecessary savings
    _need_to_save = False

    # helper function for walking through the JSON
    def _walk(self, obj):
        if isinstance(obj, list):
            for list_item in obj:
                self._walk(list_item)
        elif isinstance(obj, dict):
            if 'source' in obj:
                if obj['source'].startswith('http://base'):
                    label_de = get_preflabel_via_uri(obj['source'], lang='de')
                    label_en = get_preflabel_via_uri(obj['source'], lang='en')
                    if settings.EN_LABELS_TITLE_CASE:
                        label_en = titlecase(label_en)
                    if 'label' not in obj:
                        obj['label'] = {}
                    if obj['label'].get('de') != label_de:
                        obj['label']['de'] = label_de
                        self._need_to_save = True
                    if obj['label'].get('en') != label_en:
                        obj['label']['en'] = label_en
                        self._need_to_save = True
                if 'roles' in obj:
                    self._walk(obj['roles'])
            else:
                for _k, v in obj.items():
                    self._walk(v)

    def handle(self, *args, **options):
        # gather all fields containing concepts
        fields_to_update = []
        model_fields = Entry._meta.fields
        for field in model_fields:
            if isinstance(field, JSONField):
                fields_to_update.append(field.name)

        for e in progressbar(Entry.objects.all()):
            for field in fields_to_update:
                self._walk(getattr(e, field))
            if self._need_to_save:
                e.save()
                self._need_to_save = False
