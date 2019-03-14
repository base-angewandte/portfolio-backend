from marshmallow import Schema, fields

from .general import ContributorSchema, DateSchema, DateTimeSchema, LocationSchema
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
    winner = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'winner'  # TODO: replace with id!
    }})
    granted_by = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'granted_by'  # TODO: replace with id!
    }})
    jury = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'jury'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
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
