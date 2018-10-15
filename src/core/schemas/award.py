from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Wettbewerb',
    'artist in residence',
]


class AwardSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    category = fields.Str()
    winner = fields.Nested(PersonSchema)
    granted_by = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()
