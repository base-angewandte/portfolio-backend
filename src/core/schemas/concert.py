from marshmallow import Schema, fields

from .general import ContributorSchema, DateTimeSchema, GEOReferenceSchema

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
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False, **{'x-attrs': {
        'order': 2,
        'field_type': 'autocomplete',
        'source': 'http://localhost:8200/autosuggest/v1/place/'
    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text'}})


class ConcertSchema(Schema):
    musician = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'musician'  # TODO: replace with id!
    }})
    composer = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'composer'  # TODO: replace with id!
    }})
    conductor = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'conductor'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date_location = fields.List(fields.Nested(DateTimeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 6}})
