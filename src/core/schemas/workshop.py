from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Kinderunikunst',
    'Weiterbildung',
    'Kurs',
    'Seminar',
    'postgraduales Studienangebot',
    'Doktoratsstudium',
    'Einzelcoaching',
    'individuelle Maßnahme',
    'projektorientierte Lehrtätigkeit',
    'Interdisziplinäre Lehrtätigkeit',
    'Interdisziplinäre / projektorientierte Lehrtätigkeit',
]


class WorkshopSchema(Schema):
    organiser = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'organiser'  # TODO: replace with id!
    }})
    lecturer = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'lecturer'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 5}})
