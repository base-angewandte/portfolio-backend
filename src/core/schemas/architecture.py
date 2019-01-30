from marshmallow import Schema, fields

from .general import ContributorSchema, DateLocationSchema

# TODO use concept ids as keys
TYPES = [
    'Gebäude',
    'Bau',
    'Struktur',
    'Architekturdesign',
    'Statik',
    'Architekturmodell',
    'Architekturentwurf',
    'Architekturprojekt',
]


class ArchitectureSchema(Schema):
    architect = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'architect'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date = fields.List(fields.Nested(DateLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'group',
        'show_label': False,
    }})
    material = fields.Str(**{'x-attrs': {
        'order': 4,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    format = fields.Str(**{'x-attrs': {
        'order': 5,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    url = fields.Str(**{'x-attrs': {
        'order': 6,
        'field_type': 'text',
    }})
