from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, DateSchema, DateTimeSchema, LocationSchema, get_contributors_field, \
    get_contributors_field_for_role
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Wettbewerb',
    'artist in residence',
    'Preis',
    'Auszeichnung',
    'Nominierung',
]


class AwardSchema(Schema):
    category = fields.Str(**{'x-attrs': {'order': 1}})
    winner = get_contributors_field_for_role('winner', {'order': 2})
    granted_by = get_contributors_field_for_role('granted_by', {'order': 3})
    jury = get_contributors_field_for_role('jury', {'order': 4})  # TODO: not sortable according to objects and forms
    contributors = get_contributors_field({'order': 5})
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {
        'order': 6,
        'field_type': 'date',
        'field_format': 'half',
    }})
    award_ceremony = fields.Nested(DateTimeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 7,
        'field_type': 'date',
        'field_format': 'half',
    }})
    location = fields.Nested(LocationSchema, additionalProperties=False, **{'x-attrs': {
        'order': 8,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 9}})
