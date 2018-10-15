from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Teaching',
]


class TeachingSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    instructor = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
