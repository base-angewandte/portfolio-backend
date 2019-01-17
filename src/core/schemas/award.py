from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema

# TODO use concept ids as keys
TYPES = [
    'Wettbewerb',
    'artist in residence',
]


class AwardSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    category = fields.Str()
    winner = fields.Nested(PersonSchema, additionalProperties=False)
    granted_by = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
