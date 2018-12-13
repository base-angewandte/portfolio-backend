from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
   'Workshop',
]


class WorkshopSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    organiser = fields.Nested(PersonSchema, additionalProperties=False)
    lecturer = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
