from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema, get_contributors_field, get_contributors_field_for_role
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
    organiser = get_contributors_field_for_role('organiser_management', {'order': 1})
    lecture = get_contributors_field_for_role('lecture', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 5}})
