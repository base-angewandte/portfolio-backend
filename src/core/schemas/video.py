from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import LocationSchema, get_material_field, get_format_field, get_contributors_field, \
    get_contributors_field_for_role, get_date_field, get_url_field

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
    director = get_contributors_field_for_role('director', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    published_in = fields.Str(**{'x-attrs': {
        'order': 3,
        'field_type': 'autocomplete',
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
        'field_format': 'half',
    }})
    date = get_date_field({'order': 4})
    url = get_url_field({'field_format': 'half', 'order': 5})
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
    material = get_material_field({'order': 8})
    duration = fields.Str(**{'x-attrs': {'order': 9, 'field_format': 'half'}})
    format = get_format_field({'order': 10})
