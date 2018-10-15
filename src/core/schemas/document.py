from marshmallow import Schema, fields

from .general import TextSchema, PersonSchema, GEOReferenceSchema

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


class PublishedInSchema(Schema):
    title = fields.Str()
    subtitle = fields.Str()
    authors = fields.Nested(PersonSchema)
    editors = fields.Nested(PersonSchema)


class DocumentSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
    authors = fields.Nested(PersonSchema)
    editors = fields.Nested(PersonSchema)
    publisher = fields.Nested(PersonSchema)
    city = fields.Nested(GEOReferenceSchema)
    date = fields.Date()
    isbn = fields.Str()
    doi = fields.Str()
    url = fields.Str()
    published_in = fields.Nested(PublishedInSchema)
    volume = fields.Str()
    pages = fields.Str()
    participants = fields.Nested(PersonSchema, many=True)
    language = fields.Str()
    material = fields.Str()
    format = fields.Str()
    extent = fields.Str()
    edition = fields.Str()
