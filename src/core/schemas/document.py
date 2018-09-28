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
        validate=validate.OneOf(
            settings.LANGUAGES_DICT.keys(),
            labels=settings.LANGUAGES_DICT.values(),
        ),
        required=True,
    )
    text = fields.Str(required=True)
    type = fields.Str()


class DocumentSchema(Schema):
    text = fields.Nested(TextSchema, many=True, required=False)
