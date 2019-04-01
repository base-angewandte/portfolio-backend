from marshmallow import Schema, fields

from .general import DateRangeLocationSchema, get_contributors_field, get_contributors_field_for_role, get_url_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Festival',
]


class FestivalSchema(Schema):
    organiser = get_contributors_field_for_role('organiser_management', {'order': 1})
    artist = get_contributors_field_for_role('artist', {'order': 2})
    curator = get_contributors_field_for_role('curator', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False, **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }}))
    url = get_url_field({'order': 5})
