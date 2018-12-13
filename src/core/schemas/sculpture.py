from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, InstitutionSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Sculpture',
]


class SculptureSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    artist = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    participating_institutions = fields.List(fields.Nested(InstitutionSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    material = fields.Str()
    format = fields.Str()
    dimensions = fields.Str()
    url = fields.Str()
