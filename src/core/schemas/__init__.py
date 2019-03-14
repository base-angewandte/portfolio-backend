import importlib
import json

from apispec.ext.marshmallow.openapi import OpenAPIConverter
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _
from rest_framework.utils.encoders import JSONEncoder

from .general import TextsModelSchema, KeywordsModelSchema

if not settings.OPEN_API_VERSION or not settings.ACTIVE_SCHEMAS:
    raise ImproperlyConfigured(_('Schemas improperly configured'))

ICON_DEFAULT = static('img/sheet-empty.svg')
ICON_EVENT = static('img/calendar-number.svg')

ACTIVE_TUPLES = []
ACTIVE_TYPES = []

for schema in settings.ACTIVE_SCHEMAS:
    s = importlib.import_module('.{}'.format(schema), __name__)
    ACTIVE_TUPLES.append(
        (
            s.TYPES,
            getattr(s, '{}Schema'.format(''.join(x.capitalize() for x in schema.split('_')))),
            s.ICON if hasattr(s, 'ICON') else ICON_DEFAULT,
        )
    )
    ACTIVE_TYPES += [*s.TYPES]


ACTIVE_TYPES_CHOICES = [
    [i, _(i)] for i in ACTIVE_TYPES  # TODO change _ to get_preflabel_lazy as soon as TYPES are concept ids
]

if len(set(ACTIVE_TYPES)) < len(ACTIVE_TYPES):
    raise ImproperlyConfigured(_('Active schemas contain duplicate types'))


converter = OpenAPIConverter(settings.OPEN_API_VERSION)


def schema2jsonschema(schema, force_text=False):
    jsonschema = converter.schema2jsonschema(schema)
    jsonschema['additionalProperties'] = False
    if force_text:
        # this is kinda hacky - change it if there's a better solution to force evaluation of lazy objects
        # inside a dict
        jsonschema = json.loads(json.dumps(jsonschema, cls=JSONEncoder))
    return jsonschema


def get_jsonschema(entry_type, force_text=False):
    for t, s, i in ACTIVE_TUPLES:
        if entry_type in t:
            return schema2jsonschema(s, force_text)


def get_icon(entry_type):
    for t, s, i in ACTIVE_TUPLES:
        if entry_type in t:
            return i


def get_keywords_jsonschema():
    return schema2jsonschema(KeywordsModelSchema, force_text=True)['properties']['keywords']


def get_texts_jsonschema():
    return schema2jsonschema(TextsModelSchema, force_text=True)['properties']['texts']
