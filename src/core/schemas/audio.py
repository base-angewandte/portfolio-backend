from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, LocationSchema, DateSchema, get_material_field, get_format_field, \
    get_contributors_field, get_contributors_field_for_role

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
    authors = get_contributors_field_for_role('authors', {'order': 1})
    artist = get_contributors_field_for_role('artist', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    published_in = fields.Str(**{'x-attrs': {
        'order': 4,
        'field_type': 'autocomplete',
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
    }})
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {'order': 5, 'field_type': 'date', 'field_format': 'half'}})
    language = fields.List(fields.Str(), **{'x-attrs': {
        'order': 6,
        'field_type': 'chips',
        'source': 'vocbench',
        'field_format': 'half',
    }})
    url = fields.Str(**{'x-attrs': {'order': 7}})
    location = fields.List(fields.Nested(LocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 8,
        'field_type': 'group',
        'show_label': False,
    }})
    material = get_material_field({'order': 9})
    duration = fields.Str(**{'x-attrs': {'order': 10, 'field_format': 'half'}})
    format = get_format_field({'order': 11})
