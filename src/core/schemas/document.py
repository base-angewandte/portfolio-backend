from django.conf import settings
from marshmallow import Schema, fields, validate

# TODO use english translation as keys instead of german
TYPES = [
    'Monographie',
    'Periodikum',
    'Sammelband',
    'Aufsatzsammlung',
    'Künstlerbuch',
    'Zeitungsbericht',
    'Interview',
    'Artikel',
    'Kolumne',
    'Blog',
    'Ausstellungskatalog',
    'Katalog',
    'Rezension',
    'Kritik',
    'Kapitel',
    'Konferenzschrift',
    'Aufsatz',
    'Masterarbeit',
    'Diplomarbeit',
    'Dissertation',
    'Bachelorarbeit',
    'Essay',
    'Studie',
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

class PublishedInSchema(Schema):
    title = fields.Str()
    subtitle = fields.Str()
    authors = fields.Nested(PersonSchema())
    editors = fields.Nested(PersonSchema())

class DocumentSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    authors = fields.Nested(PersonSchema())
    editors = fields.Nested(PersonSchema())
    publisher = fields.Nested(PersonSchema())
    city = fields.Nested(GEOReferenceSchema())
    date = fields.Date()
    isbn = fields.Str()
    doi = fields.Str()
    url = fields.Str()
    published_in = fields.Nested(PublishedInSchema())
    volume = fields.Str()
    pages = fields.Str()
    participants = fields.Nested(PersonSchema(), many=True)
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
    extent = fields.Str()
    edition = fields.Str()
