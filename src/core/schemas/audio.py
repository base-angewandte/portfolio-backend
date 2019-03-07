from marshmallow import Schema, fields

from .general import ContributorSchema, LocationSchema, DateSchema

# TODO use concept ids as keys
TYPES = [
    'Podcast',
    'Radiointerview',
    'Radiofeature',
    'Radiobeitrag',
    'Audiobeitrag',
    'Reportage',
    'Hörspiel',
    'Hörbuch',
    'Rundfunkausstrahlung',
    'Radiokunst',
    'Konzertmitschnitt',
    'Studioeinspielung',
    'Tonaufnahme',
    'Audioaufzeichnung',
    'mp3',
    'Kammermusik CD',
    'CD Aufnahme',
    'Album',
    'CD-Box',
]


class AudioSchema(Schema):
    author = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'sortable': True,
        'default_role': 'author',  # TODO: replace with id!
        'placeholder': 'Wähle Autor*innen',
    }})
    artist = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'sortable': True,
        'default_role': 'artist',  # TODO: replace with id!
        'placeholder': 'Wähle Künstler*innen',
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'placeholder': 'Wähle beteiligte Personen oder Institutionen aus',
    }})
    published_in = fields.Str(**{'x-attrs': {
        'order': 3,
        'field_type': 'autocomplete',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {'order': 4, 'field_type': 'date', 'field_format': 'half'}})
    language = fields.List(fields.Str(), **{'x-attrs': {
        'order': 5,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
    }})
    url = fields.Str(**{'x-attrs': {'order': 6}})
    location = fields.List(fields.Nested(LocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 7,
        'field_type': 'group',
        'show_label': False,
    }})
    material = fields.List(fields.Str(), **{'x-attrs': {
        'order': 8,
        'field_type': 'chips',
        'source': 'vocbench',
        'sortable': True,
    }})
    duration = fields.Str(**{'x-attrs': {'order': 9, 'field_format': 'half'}})
    format = fields.List(fields.Str(), **{'x-attrs': {
        'order': 10,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
        'sortable': True,

    }})
