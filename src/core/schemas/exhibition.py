from marshmallow import Schema, fields

from .general import get_contributors_field, get_contributors_field_for_role, get_location_field, get_url_field, \
    get_date_range_field, get_date_time_range_field, get_location_description_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Einzelausstellung',
    'Gruppenausstellung',
    'Vernissage',
    'Finissage',
    'Messe-Präsentation',
    'Retrospektive',
    'Soloausstellung',
    'Werkschau',
]


class DateOpeningLocationSchema(Schema):
    date = get_date_range_field({'order': 1, 'field_format': 'full'})
    opening = get_date_time_range_field({'order': 2})
    location = get_location_field({'order': 3})
    location_description = get_location_description_field({'field_format': 'half', 'order': 4})


class ExhibitionSchema(Schema):
    artist = get_contributors_field_for_role('artist', {'order': 1})
    curator = get_contributors_field_for_role('curator', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date = fields.List(
        fields.Nested(DateOpeningLocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'field_type': 'group',
            'order': 4,
            'show_label': False,
        }},
    )
    url = get_url_field({'order': 5})
