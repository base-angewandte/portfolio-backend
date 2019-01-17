from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema, InstitutionSchema

# TODO use concept ids as keys
TYPES = [
    'Installation',
]


class InstallationSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    artist = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    participating_institutions = fields.List(fields.Nested(InstitutionSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    material = fields.Str()
    format = fields.Str()
    dimensions = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
    url = fields.Str()
