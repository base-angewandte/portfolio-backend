from apispec.ext.marshmallow.openapi import OpenAPIConverter
from django.utils.translation import ugettext_lazy as _

from .document import DocumentSchema, TYPES as DOCUMENT_TYPES

converter = OpenAPIConverter('2.0')


def get_jsonschema(entity_type):
    if entity_type in DOCUMENT_TYPES:
        return converter.schema2jsonschema(DocumentSchema)


ACTIVE_TYPES = [
    *DOCUMENT_TYPES,
]

ACTIVE_TYPES_CHOICES = [
    [i, _(i)] for i in ACTIVE_TYPES
]
