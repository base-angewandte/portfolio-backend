from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, GEOReferenceSchema, DateRangeSchema, DateTimeSchema, get_contributors_field, \
    get_contributors_field_for_role
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Einzelausstellung',
    'Gruppenausstellung',
    'Vernissage',
    'Finissage',
    'Messe-Präsentation',
    'Retrospektive',
    'Soloausstellung',
    'Werkschau',
]


class DateOpeningLocationSchema(Schema):
    date = fields.Nested(DateRangeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 1,
        'field_type': 'date',
        'field_format': 'half',
    }})
    opening = fields.Nested(DateTimeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 2,
        'field_type': 'date',
        'field_format': 'half',
    }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
        'field_format': 'half',
    }})
    location_description = fields.String(**{'x-attrs': {'order': 4, 'field_type': 'text', 'field_format': 'half'}})


class ExhibitionSchema(Schema):
    artist = get_contributors_field_for_role('artist', {'order': 1})
    curator = get_contributors_field_for_role('curator', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date = fields.List(fields.Nested(DateOpeningLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 5}})
