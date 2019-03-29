from django.urls import reverse_lazy
from marshmallow import Schema, fields

from core.skosmos import get_preflabel_lazy, get_uri
from .general import ContributorSchema, LocationSchema, DateSchema, DateLocationSchema, get_material_field, \
    get_format_field, get_contributors_field, get_contributors_field_for_role

# TODO use concept ids as keys
TYPES = [
    'Fotografie',
    'Gemälde',
    'Zeichnung',
    'Collage',
    'Druckgrafik',
    'Ausstellungsansicht',
    'Werkabbildung',
    'Videostill',
    'Mixed Media',
    'Kunst am Bau',
]


class ImageSchema(Schema):
    artist = get_contributors_field_for_role('artist', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_location = fields.List(
        fields.Nested(DateLocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'order': 3,
            'field_type': 'group',
            'show_label': False,
        }}
    )
    material = get_material_field({'order': 4})
    format = get_format_field({'order': 5})
    dimensions = fields.Str(**{'x-attrs': {'order': 8, 'field_format': 'half'}})
    url = fields.Str(**{'x-attrs': {'order': 5, 'field_format': 'half'}})
