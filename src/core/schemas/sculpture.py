from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema

# TODO use concept ids as keys
TYPES = [
    'Installation',
    'Auftragsarbeit',
    'Kunst im öffentlichen Raum',
    'Skulptur',
    'Plastik',
    'Keramik',
    'Textil',
    'Schmuck',
]


class SculptureSchema(Schema):
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
    material = fields.List(fields.Str(), **{'x-attrs': {
        'order': 4,
        'field_type': 'chips',
        'source': 'vocbench',
    }})
    format = fields.List(fields.Str(), **{'x-attrs': {
        'order': 5,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half'
    }})
    dimensions = fields.Str(**{'x-attrs': {
        'order': 6,
        'field_type': 'text',
        'field_format': 'half'
    }})
    url = fields.Str(**{'x-attrs': {
        'order': 7,
        'field_type': 'text',
    }})
