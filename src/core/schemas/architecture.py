from marshmallow import Schema, fields

from .general import DateLocationSchema, get_material_field, get_format_field, get_contributors_field, \
    get_contributors_field_for_role, get_url_field

# TODO use concept ids as keys
TYPES = [
    'Gebäude',
    'Bau',
    'Struktur',
    'Architekturdesign',
    'Statik',
    'Architekturmodell',
    'Architekturprojekt',
]


class ArchitectureSchema(Schema):
    architecture = get_contributors_field_for_role('architecture', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_location = fields.List(fields.Nested(DateLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 3,
        'field_type': 'group',
        'show_label': False,
    }})
    material = get_material_field({
        'field_format': 'half',
        'order': 4,
    })
    format = get_format_field({'order': 5})
    url = get_url_field({'order': 6})
