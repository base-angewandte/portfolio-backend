from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use concept ids as keys
TYPES = [
    'Fernsehbericht',
    'Dokumentation',
    'Spielfilm',
    'Film',
    'Fernsehbeitrag',
    'TV-Beitrag',
]


class VideoSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    director = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    tv_station = fields.Str()
    city = fields.Nested(GEOReferenceSchema, additionalProperties=False)
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    duration = fields.Str()
    material = fields.Str()
    format = fields.Str()
