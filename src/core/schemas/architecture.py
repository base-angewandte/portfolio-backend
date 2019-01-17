from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, InstitutionSchema, GEOReferenceSchema

# TODO use concept ids as keys
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
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    architect = fields.Nested(PersonSchema, additionalProperties=False)
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    participating_institutions = fields.List(fields.Nested(InstitutionSchema, additionalProperties=False))
    keywords = fields.Str()
    date_from = fields.Date()
    date_to = fields.Date()
    material = fields.Str()
    format = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
    url = fields.Str()
