from django.conf import settings
from marshmallow import Schema, fields, validate

# TODO use english translation as keys instead of german
TYPES = [
    'General',
]

class TextSchema(Schema):
    language = fields.Str(
        # validate=validate.OneOf(
        #     #settings.LANGUAGES_DICT.keys(),
        #     #labels=settings.LANAGES_DICT.values(),
        # ),
        required=True,
    )
    text = fields.Str(required=True)
    type = fields.Str()

class PersonSchema(Schema):
    source_id = fields.Str()
    commonname = fields.Str()
    source = fields.Str()
    role = fields.Str()

class InstitutionSchema(Schema):
    source_id = fields.Str()
    commonname = fields.Str()
    source = fields.Str()
    role = fields.Str()

class ResearchProjectSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    projectlead = fields.Nested(PersonSchema())
    participants = fields.Nested(PersonSchema(), many=True)
    participatinginstitutions = fields.Nested(InstitutionSchema(), many=True)
    fundinginstitutions = fields.Nested(InstitutionSchema())
    fundingcategory = fields.Str()
    date_from = fields.Date()
    date_to = fields.Date()
    url = fields.Str()