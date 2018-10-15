from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
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
    text = fields.Nested(TextSchema, many=True, required=False)
    artist = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    radio_station = fields.Str()
    section = fields.Str()
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    duration = fields.Str()
    material = fields.Str()
    format = fields.Str()
    city = fields.Nested(GEOReferenceSchema)
