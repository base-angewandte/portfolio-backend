from marshmallow import Schema, fields

from .general import ContributorSchema, LocationSchema

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
    artist = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'artist'  # TODO: replace with id!
    }})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    published_in = fields.Str(**{'x-attrs': {
        'order': 3,
        'field_type': 'autocomplete',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date = fields.Date(**{'x-attrs': {'order': 4}})
    url = fields.Str(**{'x-attrs': {'order': 5}})
    language = fields.Str(**{'x-attrs': {
        'order': 6,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    location = fields.List(fields.Nested(LocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 7,
        'field_type': 'group',
        'show_label': False,
    }})
    duration = fields.Str(**{'x-attrs': {'order': 8}})
    material = fields.Str(**{'x-attrs': {
        'order': 8,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
    format = fields.Str(**{'x-attrs': {
        'order': 9,
        'field_type': 'autocomplete',
        'source': 'vocbench',
    }})
