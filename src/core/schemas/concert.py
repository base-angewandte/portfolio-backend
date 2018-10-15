from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Concert',
]


class ConcertSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    musician = fields.Nested(PersonSchema)
    conductor = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
