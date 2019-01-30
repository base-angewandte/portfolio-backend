from marshmallow import Schema, fields

from .general import ContributorSchema, GEOReferenceSchema, DateSchema

# TODO use concept ids as keys
TYPES = [
    'Monographie',
    'Periodikum',
    'Sammelband',
    'Aufsatzsammlung',
    'Künstlerbuch',
    'Zeitungsbericht',
    'Interview',
    'Zeitungsartikel',
    'Kolumne',
    'Blog',
    'Ausstellungskatalog',
    'Katalog',
    'Rezension',
    'Kritik',
    'Beitrag in Sammelband',
    'Aufsatz',
    'Beitrag in Fachzeitschrift (SCI,  SSCI, A&HCI)',
    'Masterarbeit',
    'Diplomarbeit',
    'Dissertation',
    'Bachelorarbeit',
    'Essay',
    'Studie',
    'Tagungsbericht',
    'Kommentar',
    'Fanzine',
    'Buchreihe',
    'Schriftenreihe',
    'Edition',
    'Drehbuch',
    'Libretto',
    'Gutachten',
    'Clipping',
    'Zeitschrift',
    'Magazin',
    'Archivalie',
    'Printbeitrag',
    'Onlinebeitrag',
    'wissenschaftliche Veröffentlichung',
    'künstlerische Veröffentlichung',
    'Katalog/künstlerisches Druckwerk',
    'künstlerischer Ton-/Bild-/Datenträger',
    'Beitrag zu künstlerischem Ton-/Bild-/Datenträger',
]


class PublishedInSchema(Schema):
    title = fields.Str(**{'x-attrs': {'order': 1}})
    subtitle = fields.Str(**{'x-attrs': {'order': 2}})
    author = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'author'  # TODO: replace with id!
    }})
    editor = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'editor'  # TODO: replace with id!
    }})
    publisher = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'publisher'  # TODO: replace with id!
    }})


class DocumentSchema(Schema):
    author = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'author'  # TODO: replace with id!
    }})
    editor = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'editor'  # TODO: replace with id!
    }})
    publisher = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'publisher'  # TODO: replace with id!
    }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'source': 'http://localhost:8200/autosuggest/v1/place/',
        'field_type': 'chips',
    }})
    date = fields.Nested(DateSchema, **{'x-attrs': {'order': 5, 'field_type': 'date'}})
    isbn = fields.Str(**{'x-attrs': {'order': 6}})
    doi = fields.Str(**{'x-attrs': {'order': 7}})
    url = fields.Str(**{'x-attrs': {'order': 8}})
    published_in = fields.List(fields.Nested(PublishedInSchema, additionalProperties=False), **{'x-attrs': {
        'order': 9,
        'field_type': 'group',
    }})
    volume = fields.Str(**{'x-attrs': {'order': 10}})
    pages = fields.Str(**{'x-attrs': {'order': 11}})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 12,
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'field_type': 'chips-below',
    }})
    language = fields.Str(**{'x-attrs': {
        'order': 13,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    material = fields.Str(**{'x-attrs': {
        'order': 14,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    format = fields.Str(**{'x-attrs': {
        'order': 15,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    edition = fields.Str(**{'x-attrs': {'order': 16}})
