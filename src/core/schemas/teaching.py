from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Teaching',
]


class TeachingSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    instructor = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
