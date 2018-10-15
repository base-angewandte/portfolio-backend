from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, InstitutionSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Sculpture',
]


class SculptureSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    artist = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    participating_institutions = fields.Nested(InstitutionSchema, many=True)
    date_from = fields.Date()
    date_to = fields.Date()
    material = fields.Str()
    format = fields.Str()
    dimensions = fields.Str()
    url = fields.Str()
