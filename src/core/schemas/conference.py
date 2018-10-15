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
    text = fields.Nested(TextSchema, many=True, required=False)
    organiser = fields.Nested(PersonSchema)
    lecturer = fields.Nested(PersonSchema)
    title_of_paper = fields.Str()
    participants = fields.Nested(PersonSchema, many=True)
    participating_institutions = fields.Nested(InstitutionSchema, many=True)
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    url = fields.Str()
    location = fields.Nested(GEOReferenceSchema)
