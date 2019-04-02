from marshmallow import Schema, fields

from .general import get_material_field, get_format_field, get_contributors_field, get_contributors_field_for_role, \
    get_url_field, get_date_location_group_field

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
    date_location = get_date_location_group_field({'order': 3})
    url = get_url_field({'field_format': 'half', 'order': 4})
    material = get_material_field({'order': 5})
    format = get_format_field({'order': 6})
    dimensions = fields.Str(**{'x-attrs': {'order': 7, 'field_format': 'half'}})
