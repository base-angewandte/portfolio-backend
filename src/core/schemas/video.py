from marshmallow import Schema, fields

from .general import ContributorSchema, DateSchema, LocationSchema

# TODO use concept ids as keys
TYPES = [
    'Fernsehbericht',
    'Dokumentation',
    'Spielfilm',
    'Film',
    'Fernsehbeitrag',
    'TV-Beitrag',
    'Kurzfilm',
    'Videoaufzeichnung',
    'Video',
    'Videoarbeit',
    'Filmarbeit',
    'Animationsfilm',
    'Experimentalfilm',
    'Trailer',
    'Dokumentarfilm',
    'DVD und Blu Ray',
    'Lehrvideo-Einleitung',
    'Lehrvideo',
    'DVD',
    'Vimeo Video',
    'Zeitbasierte Medien'
]


class VideoSchema(Schema):
    director = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'director'  # TODO: replace with id!
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
        'field_format': 'half',
    }})
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {
        'order': 4,
        'field_type': 'date',
        'field_format': 'half',
    }})
    url = fields.Str(**{'x-attrs': {'order': 5, 'field_format': 'half'}})
    language = fields.List(fields.Str(), **{'x-attrs': {
        'order': 6,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
    }})
    location = fields.List(fields.Nested(LocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 7,
        'field_type': 'group',
        'show_label': False,
    }})
    material = fields.List(fields.Str(), **{'x-attrs': {
        'order': 8,
        'field_type': 'chips',
        'source': 'vocbench',
    }})
    duration = fields.Str(**{'x-attrs': {'order': 9, 'field_format': 'half'}})
    format = fields.List(fields.Str(), **{'x-attrs': {
        'order': 10,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
    }})
