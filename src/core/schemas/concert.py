from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Concert',
]


class ConcertSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    musician = fields.Nested(PersonSchema, additionalProperties=False)
    conductor = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
