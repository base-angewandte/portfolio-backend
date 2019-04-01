from marshmallow import Schema, fields

from .general import DateTimeSchema, get_contributors_field, get_contributors_field_for_role, get_location_field, \
    get_url_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Generalprobe',
    'Soundperformance',
    'Konzert',
]


class DateTimeLocationSchema(Schema):
    date = fields.Nested(DateTimeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 1,
        'field_type': 'date',
    }})
    location = get_location_field({'order': 2})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text', 'field_format': 'half'}})


class ConcertSchema(Schema):
    music = get_contributors_field_for_role('music', {'order': 1})
    composition = get_contributors_field_for_role('composition', {'order': 2})
    conductor = get_contributors_field_for_role('conductor', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_location = fields.List(fields.Nested(DateTimeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }})
    url = get_url_field({'order': 6})
