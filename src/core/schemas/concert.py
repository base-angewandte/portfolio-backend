from marshmallow import Schema

from .general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_time_range_location_group_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Generalprobe',
    'Soundperformance',
    'Konzert',
]


class ConcertSchema(Schema):
    music = get_contributors_field_for_role('music', {'order': 1})
    conductor = get_contributors_field_for_role('conductor', {'order': 2})
    composition = get_contributors_field_for_role('composition', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_time_range_location = get_date_time_range_location_group_field({'order': 5})
    url = get_url_field({'order': 6})
