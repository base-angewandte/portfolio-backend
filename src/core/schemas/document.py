from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

# TODO use concept ids as keys
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


class PublishedInSchema(Schema):
    title = fields.Str()
    subtitle = fields.Str()
    authors = fields.Nested(PersonSchema, additionalProperties=False)
    editors = fields.Nested(PersonSchema, additionalProperties=False)


class DocumentSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, required=False, additionalProperties=False))
    authors = fields.Nested(PersonSchema, additionalProperties=False)
    editors = fields.Nested(PersonSchema, additionalProperties=False)
    publisher = fields.Nested(PersonSchema, additionalProperties=False)
    city = fields.Nested(GEOReferenceSchema, additionalProperties=False)
    date = fields.Date()
    isbn = fields.Str()
    doi = fields.Str()
    url = fields.Str()
    published_in = fields.Nested(PublishedInSchema, additionalProperties=False)
    volume = fields.Str()
    pages = fields.Str()
    participants = fields.List(fields.Nested(PersonSchema, additionalProperties=False))
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
    extent = fields.Str()
    edition = fields.Str()
