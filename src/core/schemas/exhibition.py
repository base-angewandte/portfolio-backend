from marshmallow import Schema, fields

from .general import ContributorSchema, GEOReferenceSchema, DateRangeSchema, DateTimeSchema
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
        'source': 'http://localhost:8200/autosuggest/v1/place/',
        'field_format': 'half',
    }})
    location_description = fields.String(**{'x-attrs': {'order': 4, 'field_type': 'text', 'field_format': 'half'}})


class ExhibitionSchema(Schema):
    artist = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'artist'  # TODO: replace with id!
    }})
    curator = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'curator'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date = fields.List(fields.Nested(DateOpeningLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 5}})
