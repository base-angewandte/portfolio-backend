from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use concept ids as keys
TYPES = [
    'Performance',
    'Theaterstück',
    'Aufführung',
    'Intervention',
]


class PerformanceSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    artist = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
