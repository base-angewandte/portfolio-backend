import importlib

from apispec.ext.marshmallow.openapi import OpenAPIConverter
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

if not settings.OPEN_API_VERSION or not settings.ACTIVE_SCHEMAS:
    raise ImproperlyConfigured(_('Schemas improperly configured'))

ACTIVE_TUPLES = []
ACTIVE_TYPES = []

for schema in settings.ACTIVE_SCHEMAS:
    s = importlib.import_module('.{}'.format(schema), __name__)
    ACTIVE_TUPLES.append(
        (s.TYPES, getattr(s, '{}Schema'.format(''.join(x.capitalize() for x in schema.split('_')))))
    )
    ACTIVE_TYPES += [*s.TYPES]


ACTIVE_TYPES_CHOICES = [
    [i, _(i)] for i in ACTIVE_TYPES
]

if len(set(ACTIVE_TYPES)) < len(ACTIVE_TYPES):
    raise ImproperlyConfigured(_('Active schemas contain duplicate types'))


converter = OpenAPIConverter(settings.OPEN_API_VERSION)


def get_jsonschema(entity_type):
    for t, s in ACTIVE_TUPLES:
        if entity_type in t:
            return converter.schema2jsonschema(s)
