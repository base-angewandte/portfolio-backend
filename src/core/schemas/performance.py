from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema, get_contributors_field, get_contributors_field_for_role
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Performance',
    'Theaterstück',
    'Aufführung',
    'Intervention',
    'Live Art',
    'Performance Art',
    'Solo-Performance',
    'Tanzperformance',
]


class PerformanceSchema(Schema):
    artist = get_contributors_field_for_role('artist', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 4}})
