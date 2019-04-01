from marshmallow import Schema, fields

from .general import DateLocationSchema, get_material_field, get_format_field, get_contributors_field, \
    get_contributors_field_for_role, get_url_field

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
    url = get_url_field({'field_format': 'half', 'order': 5})
