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
    text = fields.Nested(TextSchema, many=True, required=False)
    photographer = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    city = fields.Nested(GEOReferenceSchema)
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
