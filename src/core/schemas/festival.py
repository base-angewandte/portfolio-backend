from marshmallow import Schema

from .general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_range_time_range_location_group_field
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
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 5})
    url = get_url_field({'order': 6})
