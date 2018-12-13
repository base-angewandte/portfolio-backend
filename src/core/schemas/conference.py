from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema, InstitutionSchema

# TODO use english translation as keys instead of german
TYPES = [
    'Keynote',
    'Konferenzteilnahme',
    'Präsentation',
    'Symposium',
    'Tagung',
    'Veranstaltung',
    'Vortrag',
]


class ConferenceSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    organiser = fields.Nested(PersonSchema, additionalProperties=False)
    lecturer = fields.Nested(PersonSchema, additionalProperties=False)
    title_of_paper = fields.Str()
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    participating_institutions = fields.List(fields.Nested(InstitutionSchema, additionalProperties=False))
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema, additionalProperties=False)
