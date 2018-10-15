from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Einzelausstellung',
    'Gruppenausstellung',
]


class ExhibitionSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    artist = fields.Nested(PersonSchema)
    curator = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date_from = fields.Date()
    date_to = fields.Date()
    opening = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
