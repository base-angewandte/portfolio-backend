from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Fotografie',
    'Gemälde',
    'Zeichnung',
    'Collage',
]


class ImageSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    photographer = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    city = fields.Nested(GEOReferenceSchema, additionalProperties=False)
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
