from marshmallow import Schema, fields

from .general import ContributorSchema, LocationSchema, DateSchema

# TODO use concept ids as keys
TYPES = [
    'Fotografie',
    'Gemälde',
    'Zeichnung',
    'Collage',
    'Druckgrafik',
    'Ausstellungsansicht',
    'Werkabbildung',
    'Videostill',
    'Mixed Media',
    'Kunst am Bau',
]


class ImageSchema(Schema):
    artist = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'sortable': True,
        'default_role': 'artist'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    location = fields.List(fields.Nested(LocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'group',
        'show_label': False,
    }})
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {
        'order': 4,
        'field_type': 'date',
        'show_label': False,
        'field_format': 'half',
    }})
    url = fields.Str(**{'x-attrs': {'order': 5, 'field_format': 'half'}})
    material = fields.List(fields.Str(), **{'x-attrs': {
        'order': 6,
        'field_type': 'chips',
        'source': 'vocbench',
    }})
    format = fields.List(fields.Str(), **{'x-attrs': {
        'order': 7,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
    }})
    dimensions = fields.Str(**{'x-attrs': {'order': 8, 'field_format': 'half'}})
