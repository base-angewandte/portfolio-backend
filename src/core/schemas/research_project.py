from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, InstitutionSchema

# TODO use concept ids as keys
TYPES = [
    'Research Project',
]


class ResearchProjectSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    project_lead = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    participating_institutions = fields.List(fields.Nested(InstitutionSchema, additionalProperties=False))
    funding_institutions = fields.Nested(InstitutionSchema, additionalProperties=False)
    funding_category = fields.Str()
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
