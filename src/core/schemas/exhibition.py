from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use concept ids as keys
TYPES = [
    'Einzelausstellung',
    'Gruppenausstellung',
]


class ExhibitionSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    artist = fields.Nested(PersonSchema, additionalProperties=False)
    curator = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    opening = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
