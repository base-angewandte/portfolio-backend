from marshmallow import Schema

from .general import get_material_field, get_format_field, get_contributors_field, get_contributors_field_for_role, \
    get_url_field, get_date_location_group_field

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
    date_location = get_date_location_group_field({'order': 3})
    material = get_material_field({
        'field_format': 'half',
        'order': 4,
    })
    format = get_format_field({'order': 5})
    url = get_url_field({'order': 6})
