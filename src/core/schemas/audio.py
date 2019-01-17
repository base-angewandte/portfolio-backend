from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use concept ids as keys
TYPES = [
    'Podcast',
    'Radiointerview',
    'Radiofeature',
    'Radiobeitrag',
    'Audiobeitrag',
    'Reportage',
    'Hörspiel',
    'Hörbuch',
    'Rundfunkausstrahlung',
]


class AudioSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    artist = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    radio_station = fields.Str()
    section = fields.Str()
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    duration = fields.Str()
    material = fields.Str()
    format = fields.Str()
    city = fields.Nested(GEOReferenceSchema, additionalProperties=False)
