from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Fernsehbericht',
    'Dokumentation',
    'Spielfilm',
    'Film',
    'Fernsehbeitrag',
    'TV-Beitrag',
]


class VideoSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    director = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    tv_station = fields.Str()
    city = fields.Nested(GEOReferenceSchema)
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    duration = fields.Str()
    material = fields.Str()
    format = fields.Str()
