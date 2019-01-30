from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema

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
    artist = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'artist'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 4}})
