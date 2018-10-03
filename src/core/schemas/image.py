from django.conf import settings
from marshmallow import Schema, fields, validate

# TODO use english translation as keys instead of german
TYPES = [
    'Fotografie',
    'Gemälde',
    'Zeichnung',
    'Collage',
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

class GEOReferenceSchema(Schema):
    geoname_id = fields.Str()
    geoname_name = fields.Str()
    country_name = fields.Str()
    latitude = fields.Str()
    longitude = fields.Str()

class ImageSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    photographer = fields.Nested(PersonSchema())
    participants = fields.Nested(PersonSchema(), many=True)
    city = fields.Nested(GEOReferenceSchema())
    date = fields.Date()
    url = fields.Str()
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
