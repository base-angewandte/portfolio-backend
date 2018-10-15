from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
   'Workshop',
]


class WorkshopSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    organiser = fields.Nested(PersonSchema)
    lecturer = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
