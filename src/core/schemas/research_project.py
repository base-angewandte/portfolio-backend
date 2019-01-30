from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeSchema

# TODO use concept ids as keys
TYPES = [
    'Drittmittelprojekt',
    'Projekt',
    'Forschungsprojekt',
    'Artistic Research',
]


class ResearchProjectSchema(Schema):
    project_lead = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'project_lead'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    funding_institutions = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'funding_institution'  # TODO: replace with id!
    }})
    funding_category = fields.Str(**{'x-attrs': {'order': 4}})
    date = fields.Nested(DateRangeSchema, additionalProperties=False, **{'x-attrs': {'order': 5, 'field_type': 'date'}})
    url = fields.Str(**{'x-attrs': {'order': 6}})
