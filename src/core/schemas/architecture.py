from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, InstitutionSchema, GEOReferenceSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Gebäude',
    'Bau',
    'Struktur',
    'Gebäudeentwurf',
    'Entwurf',
    'Design',
    'Statik',
]


class ArchitectureSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    architect = fields.Nested(PersonSchema)
    participants = fields.Nested(PersonSchema, many=True)
    participating_institutions = fields.Nested(InstitutionSchema, many=True)
    keywords = fields.Str()
    date_from = fields.Date()
    date_to = fields.Date()
    material = fields.Str()
    format = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
    url = fields.Str()
