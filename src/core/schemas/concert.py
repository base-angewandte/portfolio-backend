from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, DateTimeSchema, GEOReferenceSchema, get_contributors_field, \
    get_contributors_field_for_role
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Generalprobe',
    'Soundperformance',
    'Konzert',
]


class DateTimeLocationSchema(Schema):
    date = fields.Nested(DateTimeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 1,
        'field_type': 'date',
    }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
        'field_format': 'half',
    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text', 'field_format': 'half'}})


class ConcertSchema(Schema):
    music = get_contributors_field_for_role('music', {'order': 1})
    composition = get_contributors_field_for_role('composition', {'order': 2})
    conductor = get_contributors_field_for_role('conductor', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_location = fields.List(fields.Nested(DateTimeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 6}})
