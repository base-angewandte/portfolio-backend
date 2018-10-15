from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Performance',
    'Theaterstück',
    'Aufführung',
    'Intervention',
]


class PerformanceSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    artist = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
